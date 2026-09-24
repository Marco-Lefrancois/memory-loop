import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.state import LoopState
from src.pipelines.ingest_agent import IngestAgent

def test_ingest_agent_handles_error_without_caching(tmp_path):
    state = LoopState(project_name="TestProject")
    test_file = tmp_path / "corrupt_file.xlsx"
    test_file.write_bytes(b"dummy data")

    agent = IngestAgent()

    # Patcher try_markitdown tel qu'il est importé dans ingest_agent (pas _try_markitdown)
    # et _parse_xlsx sur la classe pour simuler un XLSX illisible
    with patch("src.pipelines.ingest_agent.try_markitdown", return_value=""):
        with patch.object(IngestAgent, "_parse_xlsx", return_value="[Erreur : openpyxl n'est pas installé. Lecture XLSX impossible]"):
            with patch("src.pipelines.ingest_agent.ZeroFluffConsole.error") as mock_error:
                result_state = agent._process_file(test_file, state)

                # Vérifie que ZeroFluffConsole.error a bien été appelé
                assert mock_error.called
                # Vérifie que le fichier en échec n'a PAS été ajouté à ingested_sources
                assert len(result_state.ingested_sources) == 0
