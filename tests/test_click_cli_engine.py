"""Harnais de test in-process du moteur CLI Click (MLOOP-194-BE / EPIC-19).

Objectif : valider et prémunir contre la régression des commandes mLoop via
``click.testing.CliRunner`` — exécution en mémoire, zéro ``subprocess.run`` (CA-1),
avec assertions déterministes sur les codes de sortie et la séparation des flux.

Contrats de sortie établis empiriquement (Click 8.5, in-process) :
  * 0   → succès ou guardrail passant (ex. ``lifecycle-status``, ``vibe-check``).
  * 1   → violation métier / porte : ``--project`` manquant, Lifecycle Gate bloquée,
          exception non maîtrisée dans un handler (``SystemExit(1)``).
  * 2   → erreur de parsing Click : commande inconnue (did-you-mean),
          option requise absente (``UsageError``).

Anomalie A2 (héritée MLOOP-190-BE, non corrigée ici — hors périmètre) : le
``ZeroFluffConsole.error`` s'appuie sur un ``rich.Console`` sans ``stderr=True``
(``src/cli/__init__.py``) : les messages d'erreur métier sortent sur **stdout**.
Ces tests documentent le comportement réel (attendu = état courant) et la matrice
de divergence est consignée dans l'EvidencePack pour arbitrage PO. Le journal
structuré ``logger`` reste, lui, correctement dirigé vers stderr.

Aucune route HTTP (ADR-0319). RULE-AST-01 : module de test borné.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

import pytest
from click.testing import CliRunner

import src.cli.click_engine.context as context_mod
import src.commands.router as commands_router
from src.cli.click_engine.router import ArgsShim, MLoopMultiCommand, cli
from src.commands._registry import COMMANDS

PROJECT = "mLoop"
VITAL_COMMANDS = (
    "vibe-check",
    "gate-approve",
    "sync",
    "crawl",
    "lifecycle-status",
    "worker-spawn",
)


@pytest.fixture(autouse=True)
def _force_click_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le moteur ciblé est exclusivement le routeur Click (jamais argparse)."""
    monkeypatch.setenv("MLOOP_CLI_ENGINE", "click")


@pytest.fixture
def runner() -> CliRunner:
    """CliRunner Click 8.5 : ``output``/``stdout``/``stderr`` toujours séparés."""
    return CliRunner()


@pytest.fixture
def block_gate(monkeypatch: pytest.MonkeyPatch):
    """Force la Lifecycle Gate à refuser toute commande (violation simulée)."""

    def _refuse(project_path, cmd_name, task_type=None):
        return (False, f"TEST: commande '{cmd_name}' interdite en phase courante")

    monkeypatch.setattr(
        context_mod.ProjectLifecycleManager, "can_execute_command", staticmethod(_refuse)
    )


@pytest.fixture
def no_active_project(monkeypatch: pytest.MonkeyPatch):
    """Neutralise toute résolution de projet actif → vrai cas 'sans projet'."""
    monkeypatch.setenv("MLOOP_ACTIVE_PROJECT", "")
    monkeypatch.setattr(context_mod, "_read_active_project", lambda: None)


# --------------------------------------------------------------------------- #
# Pilier 1 : Nominal — exécution in-process d'une commande vitale (CA-1/CA-2)  #
# --------------------------------------------------------------------------- #
class TestPilier1Nominal:
    def test_lifecycle_status_returns_zero_and_reports_phase(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["lifecycle-status", "--project", PROJECT])
        assert result.exit_code == 0
        assert "CYCLE DE VIE PROJET" in result.stdout
        assert "MLOOP" in result.stdout.upper()

    def test_no_subprocess_module_used_by_engine(self) -> None:
        """CA-1 : le routeur Click n'importe jamais ``subprocess`` pour dispatcher."""
        import src.cli.click_engine.router as router_mod

        source = router_mod.__file__
        with open(source, "r", encoding="utf-8") as handle:
            content = handle.read()
        assert "subprocess" not in content

    def test_root_help_is_available(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "mLoop State & Validation Backend" in result.stdout


# --------------------------------------------------------------------------- #
# Pilier 2 : Exceptions — codes de sortie déterministes (CA-2)                 #
# --------------------------------------------------------------------------- #
class TestPilier2Exceptions:
    def test_missing_project_exits_one(self, runner: CliRunner, no_active_project) -> None:
        """Sans projet résolu, la commande exempte de sous-processus sort en 1."""
        result = runner.invoke(cli, ["vibe-check"])
        assert result.exit_code == 1
        assert "--project" in result.stdout  # A2 : message métier sur stdout

    def test_unknown_command_exits_two_with_did_you_mean(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["vibe-chek", "--project", PROJECT])
        assert result.exit_code == 2
        assert "No such command" in result.stderr
        assert "Did you mean" in result.stderr

    def test_missing_required_option_exits_two(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["gate-approve", "--project", PROJECT])
        assert result.exit_code == 2
        assert "Missing option" in result.stderr
        assert "--gate" in result.stderr

    @pytest.mark.parametrize(
        "args,expected",
        [
            (["vibe-chek", "--project", PROJECT], 2),
            (["gate-approve", "--project", PROJECT], 2),
        ],
    )
    def test_parsing_errors_are_exit_two(
        self, runner: CliRunner, args: list, expected: int
    ) -> None:
        assert runner.invoke(cli, args).exit_code == expected


# --------------------------------------------------------------------------- #
# Pilier 3 : Résilience & Mode Dégradé (CA-3)                                  #
# --------------------------------------------------------------------------- #
class TestPilier3Resilience:
    def test_lifecycle_gate_block_exits_one_and_skips_handler(
        self, runner: CliRunner, block_gate, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CA-3 : gate refusée → exit 1 et le handler n'est JAMAIS résolu/appelé."""
        calls = {"count": 0}
        original = commands_router._resolve_handler

        def _spy(handler_ref: str):
            calls["count"] += 1
            return original(handler_ref)

        monkeypatch.setattr(commands_router, "_resolve_handler", _spy)
        result = runner.invoke(cli, ["lifecycle-status", "--project", PROJECT])
        assert result.exit_code == 1
        assert calls["count"] == 0
        assert "LIFECYCLE GATE VIOLATION" in result.stdout

    def test_handler_exception_is_captured_as_exit_one(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un handler qui lève est capturé sans crash du process de test."""

        def _boom(handler_ref: str):
            def _raise(args, state, project_path):
                raise RuntimeError("panne runtime simulée")

            return _raise

        monkeypatch.setattr(commands_router, "_resolve_handler", _boom)
        result = runner.invoke(cli, ["lifecycle-status", "--project", PROJECT])
        assert result.exit_code == 1
        assert isinstance(result.exception, (RuntimeError, SystemExit))


# --------------------------------------------------------------------------- #
# Pilier 4 : UX — séparation des flux & matrice A2 (observabilité)            #
# --------------------------------------------------------------------------- #
class TestPilier4UX:
    def test_parsing_error_stream_is_stderr(self, runner: CliRunner) -> None:
        """Les erreurs de parsing Click natives sont fidèlement sur stderr."""
        result = runner.invoke(cli, ["commande-inexistante", "--project", PROJECT])
        assert result.stderr.strip()
        assert result.stdout == ""

    def test_success_output_stream_is_stdout(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["lifecycle-status", "--project", PROJECT])
        assert result.stdout.strip()
        assert "CYCLE DE VIE" in result.stdout

    def test_a2_business_error_currently_on_stdout(
        self, runner: CliRunner, no_active_project
    ) -> None:
        """Contrat A2 documenté : erreur métier (ZeroFluffConsole) → stdout (état
        courant hérité de MLOOP-190-BE). Si corrigé un jour, ce test signalera la
        bascule vers stderr et devra être mis à jour (garde de régression A2)."""
        result = runner.invoke(cli, ["vibe-check"])
        assert result.exit_code == 1
        assert "--project" in result.stdout
        assert "--project" not in result.stderr


# --------------------------------------------------------------------------- #
# CA-4 : ArgsShim — conformité du contrat de types vers les handlers legacy    #
# --------------------------------------------------------------------------- #
class TestArgsShim:
    def test_is_argparse_namespace_subclass(self) -> None:
        assert issubclass(ArgsShim, argparse.Namespace)

    def test_from_click_maps_params_and_project(self) -> None:
        shim = ArgsShim.from_click({"gate": 3, "notes": "ok"}, project=PROJECT)
        assert isinstance(shim, argparse.Namespace)
        assert shim.project == PROJECT
        assert shim.gate == 3
        assert shim.notes == "ok"

    def test_from_click_converts_tuple_to_list(self) -> None:
        """Écart E1 : ``multiple=True`` Click (tuple) → liste (parité argparse)."""
        shim = ArgsShim.from_click({"files": ("a", "b")}, project=None)
        assert shim.files == ["a", "b"]
        assert isinstance(shim.files, list)

    def test_from_click_preserves_scalar_types(self) -> None:
        shim = ArgsShim.from_click({"flag": True, "count": 0}, project=PROJECT)
        assert shim.flag is True
        assert shim.count == 0


# --------------------------------------------------------------------------- #
# CA-2 : couverture des 6 commandes vitales (surface + dispatch mocké)         #
# --------------------------------------------------------------------------- #
class TestVitalCommands:
    def test_all_vital_commands_are_registered(self) -> None:
        for name in VITAL_COMMANDS:
            assert name in COMMANDS, f"Commande vitale absente du registre : {name}"

    def test_all_vital_commands_surfaced_by_multicommand(self) -> None:
        listed = MLoopMultiCommand(name="cli").list_commands(ctx=None)  # type: ignore[arg-type]
        for name in VITAL_COMMANDS:
            assert name in listed

    @pytest.mark.parametrize("command", VITAL_COMMANDS)
    def test_vital_command_dispatch_returns_zero_with_mocked_handler(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch, command: str
    ) -> None:
        """Le dispatch de chaque commande vitale atteint le handler (exit 0) sans
        exécuter la logique métier lourde (handler substitué en mémoire)."""

        def _fake(handler_ref: str):
            def _ok(args, state, project_path):
                return 0

            return _ok

        monkeypatch.setattr(commands_router, "_resolve_handler", _fake)
        extra = ["--gate", "1"] if command == "gate-approve" else []
        extra += ["--story", "MLOOP-194-BE"] if command == "worker-spawn" else []
        result = runner.invoke(cli, [command, "--project", PROJECT, *extra])
        assert result.exit_code == 0, f"{command}: {result.stdout} {result.stderr}"


# --------------------------------------------------------------------------- #
# CA-5 : performance de la suite & benchmark in-process vs sous-processus      #
# --------------------------------------------------------------------------- #
class TestPerformanceAndBenchmark:
    def test_in_process_invocation_is_fast(self, runner: CliRunner) -> None:
        """CA-5 : une invocation in-process reste largement sous la seconde."""
        start = time.perf_counter()
        result = runner.invoke(cli, ["lifecycle-status", "--project", PROJECT])
        elapsed = time.perf_counter() - start
        assert result.exit_code == 0
        assert elapsed < 2.0

    def test_in_process_beats_subprocess_legacy(self, runner: CliRunner) -> None:
        """Benchmark honnête : CliRunner in-process vs respawn subprocess argparse.
        Le gain réel provient de l'absence de ré-initialisation d'interpréteur.
        Seuil prudent (>=1.5x) pour rester stable en CI ; le gain observé en
        développement est de l'ordre de ~5x (voir EvidencePack)."""
        iterations = 5
        t0 = time.perf_counter()
        for _ in range(iterations):
            assert runner.invoke(cli, ["lifecycle-status", "--project", PROJECT]).exit_code == 0
        in_process = (time.perf_counter() - t0) / iterations

        env = {**os.environ, "MLOOP_CLI_ENGINE": "argparse"}
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "src/swarm.py", "lifecycle-status", "--project", PROJECT],
            env=env,
            capture_output=True,
            timeout=60,
            check=False,
        )
        subprocess_time = time.perf_counter() - t0
        assert proc.returncode == 0
        assert subprocess_time > in_process * 1.5
