---
name: research
description: Conduct autonomous research by orchestrating the Deep Research Pipeline (Scout -> Crawl -> Synthesize). Integrates with mloop-crawler and Graphify.
disable-model-invocation: true
argument-hint: What topic or concept would you like to research?
---

# Deep Research Skill

The user has asked you to conduct autonomous research. This skill powers the "Deep Research Pipeline", a 3-phase collaboration between you (System 2, cognitive synthesis) and the Python backend `mloop-crawler` (System 1, data ingestion).

You MUST follow this exact 3-step workflow:

## Phase 1: Reconnaissance (Scouting)
1. Receive the research query from `CURRENT_RESEARCH.md`.
2. Use your web search or literature search plugins (e.g., arXiv) to find the best URLs, GitHub repositories, or papers relevant to the topic.
3. Write all the raw URLs you discovered into `Projects/<project_name>/reference/research/SOURCES.md`.
   - For technical documentation or software libraries, you can also use the format `- library : context7_LIBRARYNAME` to trigger context7.

## Phase 2: Aspiration (Crawling)
1. Once `SOURCES.md` is populated, you must trigger the python crawler to download the content.
2. Run the following command in the IDE terminal to invoke the `mloop-crawler`:
   ```bash
   python src/swarm.py crawl --project <project_name>
   ```
3. Wait for the command to complete. The crawler will download the sources and generate clean Markdown text in `memory/crawler/cache/`.

## Phase 3: Synthèse & Indexation (Synthesis & Sync)
1. Read the newly downloaded Markdown files from `memory/crawler/cache/`.
2. Generate a highly detailed, deeply researched `REPORT.md` inside `Projects/<project_name>/reference/research/` based on the cached contents.
3. Use strict citations pointing back to the sources.
4. Finally, synchronize the new report with Graphify by running:
   ```bash
   python src/swarm.py sync --project <project_name>
   ```
5. Append a brief summary of the new knowledge to `Projects/<project_name>/RESOURCES.md` (if part of a teach session).
