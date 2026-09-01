import os
import glob
import re

def clean_jira_markup(content: str) -> str:
    # 1. Convert Jira Headings
    content = re.sub(r'^h1\.\s+(.*)$', r'# \1', content, flags=re.MULTILINE)
    content = re.sub(r'^h2\.\s+(.*)$', r'## \1', content, flags=re.MULTILINE)
    content = re.sub(r'^h3\.\s+(.*)$', r'### \1', content, flags=re.MULTILINE)
    content = re.sub(r'^h4\.\s+(.*)$', r'#### \1', content, flags=re.MULTILINE)
    content = re.sub(r'^h5\.\s+(.*)$', r'##### \1', content, flags=re.MULTILINE)

    # 2. Convert Noformat and Code blocks
    # {code:json}...{code} -> ```json...```
    content = re.sub(r'\{code:([^}]+)\}', r'```\1\n', content)
    content = re.sub(r'\{code\}', r'```', content)
    
    # {noformat}...{noformat} -> ```gherkin...``` (defaulting to gherkin based on context)
    content = re.sub(r'\{noformat\}', '```gherkin\n', content, count=1) 
    content = re.sub(r'\{noformat\}', '```', content)
    
    # 3. Convert Monospace {{text}} -> `text`
    content = re.sub(r'\{\{([^}]+)\}\}', r'`\1`', content)
    
    # 4. Convert Links [Text|Url] -> [Text](Url)
    content = re.sub(r'\[([^|\]]+)\|([^\]]+)\]', r'[\1](\2)', content)

    # 5. Convert Bold *text* -> **text**
    content = re.sub(r'(?<!\S)\*([^\s*](?:[^*]*[^\s*])?)\*(?!\S)', r'**\1**', content)
    
    # 6. Remove Colors
    content = re.sub(r'\{color[^}]*\}', '', content)
    
    # 7. Specific typos 
    content = content.replace("## Règles d’affaires", "## Règles d'affaires")

    return content

def adjust_bullets(content: str) -> str:
    lines = content.splitlines()
    new_lines = []
    in_list = False
    h1_seen = False
    
    for line in lines:
        stripped = line.lstrip()
        
        # Numbered lists Jira (# text)
        if line.startswith("# ") and not h1_seen:
            h1_seen = True
            new_lines.append(line)
            continue
        elif line.startswith("# ") and h1_seen:
            line = "1. " + line[2:]
            stripped = line.lstrip()

        # Bullet lists
        if stripped.startswith("* "):
            bullet_content = stripped[2:]
            if bullet_content.startswith("**") or bullet_content.startswith("[") or "Règle" in bullet_content:
                in_list = True
                new_lines.append(line)
            else:
                if in_list:
                    new_lines.append("    - " + bullet_content)
                else:
                    new_lines.append(line)
                    in_list = True
        elif stripped.startswith("1. ") or stripped.startswith("2. "):
            in_list = False
            new_lines.append(line)
        elif stripped == "":
            new_lines.append(line)
        else:
            in_list = False
            new_lines.append(line)
            
    return "\n".join(new_lines)


def process_files(directory: str):
    files = glob.glob(os.path.join(directory, "**", "*.md"), recursive=True)
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        content = clean_jira_markup(content)
        content = adjust_bullets(content)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
    print(f"Jira to Markdown conversion finished on {len(files)} files.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_files(sys.argv[1])
    else:
        print("Usage: python jira_to_markdown.py <directory_path>")
