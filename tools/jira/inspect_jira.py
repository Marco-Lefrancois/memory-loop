import os
import httpx
from dotenv import load_dotenv

load_dotenv()

jira_url = os.getenv("JIRA_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
project_key = "JEANCOUTU"

auth = (jira_email, jira_token)
headers = {"Accept": "application/json"}

with httpx.Client(base_url=jira_url, auth=auth, headers=headers) as client:
    # Get issue type for sub-tasks
    r = client.get(f"/rest/api/2/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields")
    if r.status_code == 200:
        data = r.json()
        projects = data.get("projects", [])
        if projects:
            for it in projects[0].get("issuetypes", []):
                if it.get("subtask"):
                    print(f"Sub-task Type: {it.get('name')} (ID: {it.get('id')})")
                    fields = it.get("fields", {})
                    if "customfield_10151" in fields:
                        print("Field: customfield_10151 (Billing ID)")
                        allowed = fields["customfield_10151"].get("allowedValues", [])
                        print(f"  Allowed Values: {allowed}")
                    if "components" in fields:
                        print("Field: components")
                        allowed = fields["components"].get("allowedValues", [])
                        print(f"  Allowed Values: {allowed}")
    else:
        print(f"Error: {r.status_code} - {r.text}")
