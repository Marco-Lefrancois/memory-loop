"""
Tests des 4 primitives de l'extension Tasks (MLOOP-211-BE).

Couvre le contrat de service (ouverture sous budget, avancement non bloquant,
desistement borne, verdict eteint) ainsi que les regles d'affaires de
l'echeance de retention : calcul unique a l'etat terminal, recalcul a chaque
verdict depuis l'horodatage d'ouverture, et purge jamais executee.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import timedelta

import pytest

from src.bridges._mcp_tasks_service import CREATE_RESPONSE_BUDGET_S, TaskService
from src.core.task_handles import TaskError, TaskStore, utc_now
from src.core.task_lifecycle import clear_registry, transition_record


@dataclass
class FakeHandle:
    """Poignee de sous-processus factice, sans processus reel."""

    task_id: str
    subprocess_id: str = "worker_fake"
    armed: bool = False
    terminate_calls: list[float] = field(default_factory=list)
    fail_extinction: bool = False

    def arm(self) -> None:
        self.armed = True

    def terminate(self, timeout_s: float = 10.0) -> bool:
        self.terminate_calls.append(timeout_s)
        return not self.fail_extinction


@dataclass
class FakeSpawner:
    """Lanceur factice dont la lenteur simule un lancement hors budget."""

    handles: list[FakeHandle] = field(default_factory=list)
    delay_s: float = 0.0

    def launch(self, record, execution):  # noqa: ANN001 - signature du Protocol
        if self.delay_s:
            time.sleep(self.delay_s)
        handle = FakeHandle(task_id=record.task_id, subprocess_id=record.subprocess_id or "")
        self.handles.append(handle)
        return handle


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_registry()
    yield
    clear_registry()


@pytest.fixture
def store(tmp_path) -> TaskStore:
    return TaskStore("mLoop", base_dir=tmp_path / "Projects")


@pytest.fixture
def spawner() -> FakeSpawner:
    return FakeSpawner()


@pytest.fixture
def service(store, spawner) -> TaskService:
    return TaskService(store=store, spawner=spawner)


def _open(service: TaskService, story_id: str = "MLOOP-211-BE", **kwargs):
    return service.create(story_id=story_id, **kwargs)


# ── 1. Ouverture immediate ────────────────────────────────────────────────
def test_create_remits_immediatement_un_identifiant_durable(service, store, spawner):
    started = time.monotonic()
    view = _open(service)
    elapsed = time.monotonic() - started

    assert elapsed < CREATE_RESPONSE_BUDGET_S
    assert view["task_id"].startswith("task_")
    assert view["status"] == "working"
    assert view["expires_at"] is None
    assert view["subprocess_id"] == "worker_mloop_211_be"

    record = store.load(view["task_id"])
    assert record is not None
    assert record.story_id == "MLOOP-211-BE"
    assert record.expires_at is None
    assert record.created_at is not None
    # Le sous-processus n'est engage qu'apres publication de l'enregistrement.
    assert spawner.handles[0].armed is True


def test_create_rejette_le_seuil_de_reponse_immediate(service, store, spawner):
    spawner.delay_s = CREATE_RESPONSE_BUDGET_S + 0.05

    with pytest.raises(TaskError) as exc:
        _open(service)

    assert exc.value.code == "response_budget_exceeded"
    assert list(store.tasks_dir.glob("*.json")) == []
    assert list(store.tasks_dir.glob("*.tmp")) == []
    # Aucun sous-processus engage et la poignee est annulee.
    assert spawner.handles[0].armed is False
    assert spawner.handles[0].terminate_calls


def test_create_rejette_un_etat_hors_vocabulaire(service):
    with pytest.raises(TaskError) as exc:
        _open(service, status="archived")
    assert exc.value.code == "invalid_status"


def test_create_rejette_une_ouverture_sur_un_etat_terminal(service):
    with pytest.raises(TaskError) as exc:
        _open(service, status="completed")
    assert exc.value.code in ("cannot_open_on_terminal_state", "invalid_status")


def test_create_rejette_une_tache_existante(service, store):
    view = _open(service)
    with pytest.raises(TaskError) as exc:
        _open(service, task_id=view["task_id"])
    assert exc.value.code == "task_already_exists"
    assert len(list(store.tasks_dir.glob("*.json"))) == 1


def test_create_rejette_un_recit_absent(service):
    with pytest.raises(TaskError) as exc:
        _open(service, story_id="   ")
    assert exc.value.code == "missing_story_id"


def test_create_rejette_une_commande_de_lancement_inconnue(service):
    with pytest.raises(TaskError) as exc:
        _open(service, command="exec-inconnu")
    assert exc.value.code == "unsupported_command"


def test_create_peut_ouvrir_sur_input_required(service, store):
    view = _open(service, status="input_required")
    assert view["status"] == "input_required"
    assert store.load(view["task_id"]).expires_at is None


# ── 2. Avancement non bloquant ────────────────────────────────────────────
def test_status_rend_le_journal_sans_modifier_la_tache(service, store):
    view = _open(service)
    task_id = view["task_id"]
    path = store.path_for(task_id)
    before = path.read_bytes()

    result = _status(service, task_id, None)
    fresh = result["journal"]
    cursor = result["cursor"]
    record = store.load(task_id)

    assert result["status"] == "working"
    assert cursor == len(record.journal)
    assert [entry["seq"] for entry in fresh] == list(range(1, len(fresh) + 1))
    assert path.read_bytes() == before


def _status(service, task_id, since):
    return service.status_view(task_id, since)


def test_status_est_lire_incremente_sans_consommation(service):
    view = _open(service)
    task_id = view["task_id"]

    premier = service.status_view(task_id, None)
    tout, curseur_initial = premier["journal"], premier["cursor"]
    transition_record(service.store, task_id, "input_required", message="Arbitrage requis")
    second = service.status_view(task_id, curseur_initial)
    partiel, curseur_final = second["journal"], second["cursor"]

    assert len(tout) == 1
    assert len(partiel) == 1
    assert partiel[0]["status"] == "input_required"
    assert curseur_final == 2
    # La re-lecture a partir du meme curseur reste stable : ni consommation, ni altération.
    encore = service.status_view(task_id, curseur_initial)
    assert len(encore["journal"]) == 1


def test_status_rejette_un_identifiant_inconnu(service):
    with pytest.raises(TaskError) as exc:
        service.status_view("task_inconnue")
    assert exc.value.code in ("invalid_task_id", "task_not_found")


def test_status_ne_jamais_delivre_le_verdict(service):
    view = _open(service)
    result = service.status_view(view["task_id"])
    assert "verdict" not in result
    assert "deliverables" not in result


# ── 3. Desistement ────────────────────────────────────────────────────────
def test_cancel_eteint_le_sous_processus_et_renseigne_lecheance(service, spawner):
    view = _open(service)
    task_id = view["task_id"]
    handle = spawner.handles[0]

    result = service.cancel(task_id, reason="Demande devenue inutile")

    assert result["status"] == "cancelled"
    assert result["expires_at"] is not None
    assert handle.terminate_calls, "extinction bornee du sous-processus"
    record = service.store.load(task_id)
    assert record.expires_at == record.created_at + timedelta(days=7)
    assert record.payload["reason"] == "Demande devenue inutile"
    # Aucun sous-processus suivi ne subsiste apres le desistement.
    from src.core.task_lifecycle import get_handle

    assert get_handle(task_id) is None


def test_cancel_rejette_une_tache_deja_terminee(service):
    view = _open(service)
    task_id = view["task_id"]
    transition_record(service.store, task_id, "completed", payload={"deliverables": {}})
    with pytest.raises(TaskError) as exc:
        service.cancel(task_id, reason="trop tard")
    assert exc.value.code == "task_already_terminal"


def test_cancel_rejette_un_identifiant_inconnu(service):
    with pytest.raises(TaskError) as exc:
        service.cancel("task_absente", reason="x")
    assert exc.value.code in ("invalid_task_id", "task_not_found")


def test_cancel_rejette_une_extinction_non_prouvee(service, spawner):
    view = _open(service)
    spawner.handles[0].fail_extinction = True

    with pytest.raises(TaskError) as exc:
        service.cancel(view["task_id"], reason="x", timeout_s=0.05)

    assert exc.value.code == "termination_timeout"
    # Aucune ecriture partielle : la tache reste active.
    assert service.store.load(view["task_id"]).status == "working"


def test_cancel_rejette_un_sous_processus_hors_cycle_de_suivi(service):
    view = _open(service)
    from src.core.task_lifecycle import pop_handle

    pop_handle(view["task_id"])
    with pytest.raises(TaskError) as exc:
        service.cancel(view["task_id"], reason="x")
    assert exc.value.code == "subprocess_not_tracked"


# ── 4. Verdict ────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("etat", "cle"),
    [("completed", "deliverables"), ("failed", "cause"), ("cancelled", "reason")],
)
def test_result_livre_le_verdict_selon_letat_terminal(service, etat, cle):
    view = _open(service)
    task_id = view["task_id"]
    transition_record(service.store, task_id, etat, payload={cle: {"preuve": True}})

    result = service.result_view(task_id)

    assert result["status"] == etat
    assert result["verdict"][cle] == {"preuve": True}
    assert result["journal"], "journal complet restitue"


def test_result_rejette_une_tache_encore_active(service):
    view = _open(service)
    with pytest.raises(TaskError) as exc:
        service.result_view(view["task_id"])
    assert exc.value.code == "task_still_active"


def test_result_rejette_une_tache_emportee(service, store):
    with pytest.raises(TaskError) as exc:
        service.result_view("task_inconnue")
    assert exc.value.code in ("invalid_task_id", "task_not_found")


def test_result_rejette_une_echeance_depassee(service):
    view = _open(service)
    task_id = view["task_id"]
    record = transition_record(service.store, task_id, "completed", payload={"deliverables": 1})
    record.expires_at = utc_now() - timedelta(days=1)
    service.store.save(record)

    with pytest.raises(TaskError) as exc:
        service.result_view(task_id)
    assert exc.value.code == "task_expired"


def test_result_ne_modifie_ni_etat_ni_echeance(service):
    view = _open(service)
    task_id = view["task_id"]
    record = transition_record(service.store, task_id, "completed", payload={"deliverables": 1})
    path = service.store.path_for(task_id)
    before = path.read_bytes()

    service.result_view(task_id)

    after = service.store.load(task_id)
    assert after.status == "completed"
    assert after.expires_at == record.expires_at
    assert path.read_bytes() == before


# ── 5. Echeance & purge ───────────────────────────────────────────────────
def test_echeance_recalculee_a_chaque_verdict(service):
    view = _open(service)
    task_id = view["task_id"]
    ouverture = service.store.load(task_id).created_at

    premier = transition_record(service.store, task_id, "failed", payload={"cause": "boom"})
    assert premier.expires_at == ouverture + timedelta(days=7)

    second = transition_record(
        service.store,
        task_id,
        "completed",
        payload={"deliverables": 1},
        allow_terminal_to_terminal=True,
    )
    assert second.expires_at == ouverture + timedelta(days=7)


def test_etats_actifs_ne_sont_jamais_purgeables(service):
    view = _open(service, status="input_required")
    task_id = view["task_id"]
    record = service.store.load(task_id)
    assert record.expires_at is None

    with pytest.raises(TaskError) as exc:
        service.store.purge_guard(task_id)
    assert exc.value.code == "purge_refused"


def test_purge_toujours_refusee_sur_une_tache_vivante(service):
    view = _open(service)
    with pytest.raises(TaskError) as exc:
        service.store.purge_guard(view["task_id"])
    assert exc.value.code == "purge_refused"
    assert service.store.load(view["task_id"]).status == "working"


def test_purge_hors_perimetre_meme_ecoulee(service):
    view = _open(service)
    task_id = view["task_id"]
    record = transition_record(service.store, task_id, "completed", payload={"deliverables": 1})
    record.expires_at = utc_now() - timedelta(days=1)
    service.store.save(record)

    guard = service.store.purge_guard(task_id)
    assert guard["purgeable"] is True
    assert guard["deletion_executed"] is False
    assert service.store.exists(task_id), "le fichier de tache demeure intact"
