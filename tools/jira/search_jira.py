import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
import sys
import json

def main():
    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        print("Missing Jira credentials in .env")
        sys.exit(1)

    query = sys.argv[1] if len(sys.argv) > 1 else "summary ~ 'Assurance qualité' OR summary ~ 'Contrôle qualité'"
    
    auth = (jira_email, jira_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    with httpx.Client(base_url=jira_url, auth=auth, headers=headers, timeout=30.0) as client:
        r = client.get(f"/rest/api/3/search/jql?jql={query}&fields=summary,description")
        if r.status_code == 200:
            search_data = r.json()
            issues = search_data.get("issues", [])
            print(f"Found {len(issues)} issues for query: {query}")
            for issue in issues:
                print(f"- {issue.get('key')}: {issue.get('fields', {}).get('summary')}")
        else:
            print(f"Error searching Jira: {r.status_code}")
            print(r.text)

if __name__ == "__main__":
    main()
