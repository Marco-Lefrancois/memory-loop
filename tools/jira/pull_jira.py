import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
import sys

def main():
    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        print("Missing Jira credentials in .env")
        sys.exit(1)

    issue_key = sys.argv[1] if len(sys.argv) > 1 else "COUVBOIRE-630"
    
    auth = (jira_email, jira_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    with httpx.Client(base_url=jira_url, auth=auth, headers=headers, timeout=30.0) as client:
        # Use API v3 for full ADF description
        r = client.get(f"/rest/api/3/issue/{issue_key}")
        if r.status_code == 200:
            issue_data = r.json()
            fields = issue_data.get("fields", {})
            summary = fields.get("summary")
            description = fields.get("description") # ADF format in v3
            
            print(f"Summary: {summary}")
            print("Description (ADF):")
            import json
            print(json.dumps(description, indent=2))
            
            # Save to a temporary file
            out_file = Path(f"memory/jira_{issue_key}.json")
            out_file.write_text(json.dumps(issue_data, indent=2), encoding="utf-8")
            print(f"\nIssue data saved to {out_file}")
        else:
            print(f"Error fetching issue: {r.status_code}")
            print(r.text)

if __name__ == "__main__":
    main()
