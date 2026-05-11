# Phase 0 — README Skeleton & Brainstorm

## Goal
Produce a `README.md` at the repo root containing the right *headings* but mostly *placeholder content*, so Philip has a structural map of the project before any code is written. This is the rubber-duck moment.

## Inputs (must read first)
- [AGENTS.md](../AGENTS.md) — entire file, but especially:
  - §2 (assignment in one paragraph)
  - §3 (locked tech stack)
  - §6 (active decision areas) — the 14 sub-sections become 14 placeholder bullets in the "Decisions & Trade-offs" section
  - §7 (rubric mapping)
  - §8 (walkthrough cheat sheet)
- [hw.md](../hw.md) — original assignment email; specifically the `Form fields`, `Endpoints`, `Validation`, `Deliverables`, and `Definition of done` sections
- [me.md](../me.md) — developer profile (so the README's tone matches Philip)

## Deliverables
- `README.md` at the workspace root. **No other files.**

## README structure (in order)
1. **Title** — `# Eggs Unlimited — Request Eggs Form`
2. **One-line description** — what the app does and what stack it uses (e.g., "A small local FastAPI + SQLite web app for submitting and listing egg requests.")
3. **Quick Start** — placeholder code block with the four canonical steps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```
   Mark with `<!-- FILL IN PHASE 1 -->` if any pieces are not yet real.
4. **Endpoints** — markdown table with columns `Method | Path | Description`. Pre-fill the 5 required rows from §2 of AGENTS.md (`GET /`, `POST /submit`, `GET /entries`, `GET /export.csv` + alias `/exportcsv`, `GET /healthz`).
5. **Architecture diagram** — placeholder mermaid block showing the request flow:
   ```mermaid
   flowchart LR
       Browser --> FastAPI
       FastAPI --> SQLite[(entries.db)]
   ```
6. **Form fields & validation** — bullet list of the 13 fields from `hw.md`, marking which are required, the enum values for `type/size/grade/pack`, and the numeric fields. This is reference material the reviewer can spot-check.
7. **Running the tests** — placeholder `pytest -v` block, marked `<!-- FILL IN PHASE 5 -->`.
8. **Decisions & Trade-offs** — fourteen empty bullets, one per AGENTS.md §6 sub-section, each with the heading from AGENTS.md and an empty `_TODO: one-sentence why_` placeholder. Phase 6 fills these in.
9. **What I'd add with more time** — copy the bullet list from AGENTS.md §8's "What would you add with more time?" answer.
10. **Walkthrough cheat sheet** — short note saying "See [AGENTS.md §8](AGENTS.md#8-walkthrough-defense-cheat-sheet) for likely reviewer questions and answers." (AGENTS.md may or may not ship — if Philip decides not to ship it, this section gets inlined in Phase 6.)
11. **Brainstorm scratchpad** — a `<!-- BRAINSTORM -->` HTML comment block at the very bottom with prompts Philip will hand-fill before Phase 1:
    - "What's the one thing about this project I'm least sure I can defend in 30s?"
    - "Which of the 14 §6 decisions feel arbitrary, and what would I prefer to do instead?"
    - "Which form field do I expect to be hardest to validate cleanly?"

## Steps
1. Read AGENTS.md §2, §3, §6, §7, §8 in full.
2. Read hw.md's homework portion (the assignment, form fields, endpoints, validation, deliverables, definition-of-done).
3. Write `README.md` following the structure above.
4. Verify on the GitHub markdown preview (or `glow README.md` from the CLI) that all headings render and the mermaid block is well-formed.

## Exit criteria
- `README.md` exists at workspace root.
- All 11 sections above are present, in order, with the correct headings.
- The "Decisions & Trade-offs" section has exactly 14 placeholder bullets, one per AGENTS.md §6 sub-section, each with a `_TODO_` marker.
- The mermaid block is syntactically valid (no parse errors when rendered on GitHub).
- The Brainstorm scratchpad block is present and discoverable (not buried).

## Walkthrough defense notes
- The reviewer reads the README during grading. Heading hierarchy = first impression. A clean structural skeleton signals you understood the assignment before you started typing code.
- The Decisions & Trade-offs section is what earns the walkthrough points; placeholder bullets here become the script for Phase 6.

## Out of scope for this phase
- **No code.** No `app.py`, no `requirements.txt`, no `.gitignore`, no `index.html`.
- **No filled-in Decisions & Trade-offs content** — just the placeholders. Phase 6 fills them in with the *actual* reasoning after the code exists.
- **No CI badges, no license, no contributing guide** — this is a take-home, not an open-source project.
