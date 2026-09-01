import os
import httpx
from dotenv import load_dotenv

load_dotenv()

jira_url = os.getenv("JIRA_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")

auth = (jira_email, jira_token)
headers = {"Accept": "application/json"}

issue_key = "JEANCOUTU-180"

with httpx.Client(base_url=jira_url, auth=auth, headers=headers) as client:
    r = client.get(f"/rest/api/2/issue/{issue_key}")
    if r.status_code == 200:
        fields = r.json().get("fields", {})
        print(f"Issue: {issue_key}")
        print(f"Components: {fields.get('components')}")
        print(f"Billing ID (customfield_10151): {fields.get('customfield_10151')}")
        
        # Also check a sub-task if possible
        subtasks = fields.get("subtasks", [])
        if subtasks:
            sub_key = subtasks[0].get("key")
            r_sub = client.get(f"/rest/api/2/issue/{sub_key}")
            if r_sub.status_code == 200:
                sub_fields = r_sub.json().get("fields", {})
                print(f"\nSub-task: {sub_key}")
                print(f"Components: {sub_fields.get('components')}")
                print(f"Billing ID (customfield_10151): {sub_fields.get('customfield_10151')}")
    else:
        print(f"Error: {r.status_code} - {r.text}")
