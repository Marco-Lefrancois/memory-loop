import json
import pytest
from pathlib import Path
from src.cli import ZeroFluffConsole

def run_aoep_eval(project_name: str) -> dict:
    ZeroFluffConsole.info(f"Lancement de la suite d'évaluation AOEP-v0 pour '{project_name}'...")
    
    # Run test_aoep_governance.py programmatically
    test_file = Path(__file__).parent.parent.parent / "tests" / "test_aoep_governance.py"
    ret = pytest.main(["-q", str(test_file)])
    
    if ret == 0:
        obligation_pass = 100
        negative_invariant_pass = 100
        resilience_pass = 100
        status = "PASS"
    else:
        obligation_pass = 0
        negative_invariant_pass = 0
        resilience_pass = 0
        status = "FAIL"
        
    result = {
        "project": project_name,
        "aoep_score": status,
        "obligation_pass": obligation_pass,
        "negative_invariant_pass": negative_invariant_pass,
        "resilience_pass": resilience_pass
    }
    return result

if __name__ == "__main__":
    res = run_aoep_eval("mLoop")
    print(json.dumps(res, indent=2))
