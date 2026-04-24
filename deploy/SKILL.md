---
name: deploy
description: Execute a group of GitHub issues (or an ad-hoc task list) by orchestrating multiple subagents in dependency-ordered waves under a shared philosophy, committing to dev and auto-opening a PR on clean runs. Use when user says "deploy issues", "fan out", "run these in parallel", "/deploy", or wants to execute a set of prepared tasks across multiple agents at once.
---

# Deploy

**One plan. Multiple subagents. Wave-ordered execution. Single digest.**

Fan a group of prepared tasks (GitHub sub-issues or a markdown task list) out to parallel subagents, organized into dependency-ordered waves, all working under one shared philosophy. Commits land on `dev`. On a clean run, a PR opens automatically. On any failure, stop short of the PR and hand a digest back. The digest lands in the parent session so the calling Claude can pick up work afterward without re-deriving what happened.

Not for designing the plan (use `/grill-me`, `/prd-to-plan`) or creating issues (use `/decompose-issue`, `/prd-to-issues`).

## Invocation

- `/deploy` — look for a plan; if none, stop and suggest `/grill-me` first
- `/deploy --parent #N` — fan out to sub-issues of parent `#N`
- `/deploy --issues #A,#B,#C` — explicit issue list
- `/deploy --tasks ./path/to/tasks.md` — ad-hoc task list (markdown with one section per task)
- `/deploy --philosophy ./path/to/doc.md` — explicit philosophy source

## Step 1 — Establish philosophy

If `--philosophy` given, read it. Otherwise search for the most recently modified `.md` in `./prds/`, `./plans/`, `./docs/` (in that order):

```bash
find ./prds ./plans ./docs -name "*.md" -type f 2>/dev/null \
  | xargs ls -t 2>/dev/null | head -1
```

Summarize the philosophy back to the user in 2–4 bullets and ask for confirmation. Iterate until they accept.

Write the accepted philosophy to `.deploy/PHILOSOPHY.md`. If `.deploy/.gitignore` doesn't exist, create it with a single line `*`. Do not commit `.deploy/`.

## Step 2 — Gather tasks

- `--parent #N`: `gh issue view <N> --json body --jq '.body'`, parse the `## Sub-issues` checklist for `- [ ] #M — title` lines
- `--issues #A,#B,#C`: use verbatim
- `--tasks path`: read the file, split on `##` headings — each heading is a task
- No argument: try `--parent` auto-detection (most recent open parent with a `## Sub-issues` checklist); if none, stop:

  > No plan detected. Run `/grill-me` first to design the work, then `/decompose-issue` or `/prd-to-issues` to create the issues.

## Step 3 — Build the wave plan

For each task, extract two sections from its body:

- `## Files touched` — list of paths the task will write to
- `## Depends on` — optional list of task ids (e.g. `#42`)

Compute waves:

1. Task with declared deps: must wait until all deps are in a prior wave
2. Two tasks with overlapping `Files touched`: must be in different waves
3. Everything else: parallelizable

Present the plan to the user and wait for confirmation. User may edit waves freely before proceeding:

```
Proposed execution:
  Wave 1 (parallel): #A, #B, #C
  Wave 2 (parallel): #D, #E
  Wave 3 (sequential): #F
Philosophy: <one-line summary from Step 1>
Auto-PR on clean run: yes
Confirm? (y / edit)
```

## Step 4 — Prep `dev`

```bash
git fetch origin
git checkout dev 2>/dev/null || git checkout -b dev origin/main 2>/dev/null || git checkout -b dev
git pull origin dev --ff-only 2>/dev/null || true
```

All agents commit directly to `dev`. No worktrees.

## Step 5 — Execute waves

For each wave, spawn all agents in parallel in **one** Agent tool call block (multiple tool-use entries in the same assistant message). Use `subagent_type: general-purpose`.

Each subagent prompt MUST include:

1. **"Read `.deploy/PHILOSOPHY.md` first — this is the shared philosophy for this deployment. Every decision should respect it."**
2. The task body verbatim (issue body, or task section from the markdown file)
3. Instructions:
   - Work on `dev`. Commit directly to `dev` with a clear message.
   - Do your own research — read the codebase, tests, and any referenced docs.
   - Implement one thing end-to-end. Not a plan, not a research report — working code.
4. **The exact required reporting block at the end of your response** (see Step 6).

Wait for all agents in the current wave to complete before starting the next. Between waves, print:

> Wave N complete. Starting wave N+1. (ctrl-C to abort.)

**Dependency cascade:** if task `#X` fails in wave N, any task in a later wave whose `## Depends on` includes `#X` is skipped. Mark it in the digest as `skipped — dependency #X failed`. Do not spawn an agent for it.

## Step 6 — Required subagent report format

Every subagent ends its response with exactly this block (orchestrator parses by heading):

```markdown
## What I did
<2–4 sentences, plain prose>

## Files changed
- path/to/file.ext — one-line reason

## Commit
<short SHA> — <commit message>

## Decisions
- <non-obvious choice> — <why>
- (empty if none)

## Blockers
- <any failure, conflict, or skipped scope>
- (empty if clean)

## Where to look later
- path/to/file.ext:123 — what lives here now
```

A report is **clean** if `## Blockers` is empty. Otherwise it is **blocked**.

## Step 7 — Close issues

For each **clean** agent report, close its issue:

```bash
gh issue close <N> --comment "Implemented via /deploy in commit <SHA>. ✓"
```

Never close an issue whose report has non-empty `## Blockers` — the user needs to decide.

If all sub-issues under a parent are now closed, check if the parent can be closed too: `gh issue view <PARENT> --json body --jq '.body' | grep -c '\- \[ \]'` — if `0`, close with `gh issue close <PARENT> --comment "All sub-issues complete. ✓"`.

## Step 8 — Build the digest

Assemble one markdown digest:

```markdown
# Deploy run — <YYYY-MM-DD HH:MM>

**N tasks across M waves** — X clean, Y blocked.

<PR link, or "No PR opened: <reason>">

## Decisions
- [#A] <decision> — <why>
- [#B] <decision> — <why>

## Blockers
- [#C] <what happened>
- (empty if none)

## Where to look later
- [#A] path/to/file.ext:123 — what lives here now
- [#B] path/to/file.ext:45 — what lives here now

---

## Per-task reports

### #A — <title>
<full agent block>

### #B — <title>
<full agent block>
```

## Step 9 — PR gate

- **All reports clean:** open PR from `dev` → main with the digest as the body:

  ```bash
  git push origin dev
  gh pr create --base main --head dev --title "<summary>" --body "$(cat .deploy/LAST_DIGEST.md)"
  ```

- **Any blocker:** do not open a PR. Report:

  > Committed to `dev`. N of M tasks clean; Y blocked. Digest below. Review before opening a PR.

In both cases, print the full digest to the user — this is the handoff.

## Design principles (encoded here so deviations are obvious)

- **Single agent role.** Every subagent is "implement this one thing end-to-end." No multi-role orchestration.
- **Waves are the coordination mechanism.** File-overlap + explicit `## Depends on` prevent stomping. Single `dev` branch; conflicts are loud and reported.
- **Philosophy lives in a temp file**, not prompt-injected — consistent across agents, inspectable by humans.
- **Human gates at start and end only.** Start: confirm philosophy + wave plan. End: review digest, see PR.
- **"Do your best."** Failing agents don't halt the run. They report; the digest reflects failures without masking them.
- **The digest is the handoff.** `## Where to look later` specifically exists so the parent session can pick up work afterward.

## Out of scope

- Designing the plan (use `/grill-me`, `/prd-to-plan`)
- Creating issues (use `/decompose-issue`, `/prd-to-issues`)
- Multi-role agents (research / plan / execute split)
- Worktree isolation (intentionally omitted — conflicts should surface, not be masked)
