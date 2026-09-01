import os
import sys
import re
import json
import argparse

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PROSCRIBED_KEYWORDS = ["TODO", "FIXME", "TBD", "A DEFINIR", "À DÉFINIR", "[ ]"]

def evaluate_confidence(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {
            "status": "REJECT",
            "confidence_score": 0,
            "errors": [f"File not found: {file_path}"],
            "warnings": []
        }

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    score = 100
    errors = []
    warnings = []

    # 1. Check Frontmatter (40 pts)
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not frontmatter_match:
        score -= 40
        errors.append("YAML_FRONTMATTER_MISSING")
    else:
        yaml_text = frontmatter_match.group(1)
        # Pre-clean standalone dashes like `jira_key: -` into valid YAML strings
        yaml_text_cleaned = re.sub(r":\s*-\s*$", r': "-"', yaml_text, flags=re.MULTILINE)
        if HAS_YAML:
            try:
                fm_data = yaml.safe_load(yaml_text_cleaned)
                if not isinstance(fm_data, dict):
                    score -= 20
                    errors.append("YAML_FRONTMATTER_INVALID_STRUCTURE")
                else:
                    required_keys = ["id", "status", "type", "layer"]
                    missing_keys = [k for k in required_keys if k not in fm_data]
                    if missing_keys:
                        score -= 10 * len(missing_keys)
                        errors.append(f"YAML_MISSING_KEYS: {', '.join(missing_keys)}")
            except Exception as e:
                score -= 40
                errors.append(f"YAML_PARSE_ERROR: {str(e)}")
        else:
            # Fallback regex checks
            for key in ["id:", "status:", "type:", "layer:"]:
                if key not in yaml_text:
                    score -= 10
                    errors.append(f"YAML_MISSING_KEY: {key}")

    # 2. Check Gherkin Block (40 pts)
    gherkin_match = re.search(r"```gherkin\s*\n(.*?)\n```", content, re.DOTALL)
    if not gherkin_match:
        score -= 40
        errors.append("GHERKIN_BLOCK_MISSING")
    else:
        gherkin_text = gherkin_match.group(1)
        if "Fonctionnalité:" not in gherkin_text and "Feature:" not in gherkin_text:
            score -= 10
            errors.append("GHERKIN_MISSING_FEATURE_KEYWORD")
        
        scenarios = re.findall(r"(?:Scénario|Scenario)\s*:", gherkin_text, re.IGNORECASE)
        if not scenarios:
            score -= 30
            errors.append("GHERKIN_MISSING_SCENARIO_KEYWORD")
        elif len(scenarios) < 4:
            score -= 20
            errors.append(f"GHERKIN_INCOMPLETE_4_PILLARS: Found {len(scenarios)}/4 required scenarios")

    # 3. Check Proscribed Keywords (20 pts)
    found_keywords = []
    # Search for proscribed keywords outside the Gherkin block and frontmatter
    main_content = content
    if frontmatter_match:
        main_content = main_content[frontmatter_match.end():]
    
    for kw in PROSCRIBED_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", main_content, re.IGNORECASE):
            found_keywords.append(kw)

    if found_keywords:
        score -= 20
        warnings.append(f"PROSCRIBED_KEYWORDS_FOUND: {', '.join(found_keywords)}")

    final_score = max(0, score)
    status = "PASS" if final_score >= 70 and not errors else "REJECT"

    return {
        "status": status,
        "confidence_score": final_score,
        "errors": errors,
        "warnings": warnings
    }

def main():
    parser = argparse.ArgumentParser(description="Confidence Gate: Syntactic & Structural Draft Verifier")
    parser.add_argument("--file", required=True, help="Path to the Markdown file to evaluate")
    args = parser.parse_args()

    result = evaluate_confidence(args.file)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["status"] == "REJECT":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
