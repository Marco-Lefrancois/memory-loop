import json
from pathlib import Path
import sys

def adf_to_text(node):
    if not node:
        return ""
    text = ""
    if node.get("type") == "text":
        text += node.get("text", "")
    if "content" in node:
        for child in node["content"]:
            text += adf_to_text(child)
    if node.get("type") == "paragraph":
        text += "\n"
    if node.get("type") == "heading":
        text += "\n"
    if node.get("type") == "listItem":
        text += "\n- "
    return text

def main():
    data = json.loads(Path("memory/jira_COUVBOIRE-630.json").read_text(encoding="utf-8"))
    description_adf = data.get("fields", {}).get("description")
    text = adf_to_text(description_adf)
    sys.stdout.buffer.write(text.encode("utf-8"))

if __name__ == "__main__":
    main()
