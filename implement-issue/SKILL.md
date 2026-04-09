---
name: implement-issue
description: Implement a single GitHub issue end-to-end using TDD, then close it. Discovers the project's feedback loop automatically from ralph.sh, CLAUDE.md, Makefile, or package.json. Use when user says "implement issue #N", "do issue #N", "run ralph on #N", "work on issue", or wants to execute a single queued task.
---

# Implement Issue

**One issue. One Claude Code session. Full handoff.**

Implement exactly one GitHub issue with TDD, run the project's feedback loop, commit directly to `dev`, close the issue, update the local handoff file, then tell the user to end the session. The user watches and steers — this is not an autonomous loop.

## Step 0 — Branch setup

Ensure `dev` is up to date and check it out:

```bash
git fetch origin
git checkout dev 2>/dev/null || git checkout -b dev origin/main 2>/dev/null || git checkout -b dev

# Pull latest dev
git pull origin dev --ff-only 2>/dev/null || true
```

All implementation work happens directly on `dev`. Never commit to `main`.

## Step 1 — Read progress.txt and resolve the issue

If `progress.txt` exists in the project root, read it first. It contains handoff notes from the previous session — what was done, decisions made, suggested next issue. Use it to skip re-exploration.

If the user gave an issue number, use it. Otherwise pick from the suggested next issue in `progress.txt`, or:

```bash
gh issue list --label ralph --state open --json number,title --limit 1
```

Read the full issue body:

```bash
gh issue view <NUMBER> --json title,body
```

## Step 1b — Gate 1: smell check on issue text (before touching the codebase)

Read only the issue title and body. Flag obvious epics before spending any tokens on file reads.

A well-sized ralph issue has:
- One clear acceptance condition — "done" is unambiguous
- No list of multiple distinct features or behaviours
- No language like "and also", "additionally", "phase 1/2/3"

If it smells too big, stop immediately:

> "Gate 1: This issue looks oversized — it describes [X, Y, Z]. I'd recommend `/decompose-issue #N` first. Proceed anyway?"

Wait for confirmation before continuing. If confirmed, note the concern and move on.

## Step 2 — Discover the feedback loop

Check these locations in order and use the first match:

1. **`ralph.sh`** — read the `feedback_loop()` function and the `DONE CONDITION` block in the claude prompt
2. **`CLAUDE.md`** — look for a "feedback loop" or "done condition" section
3. **`Makefile`** — look for `test`, `check`, or `verify` targets
4. **`package.json`** — look for `test` or `lint` scripts
5. **Ask the user** if none found

For this project (`TowerDefenseSequel`), the feedback loop is:
```bash
# Godot is flatpak on this machine — use full invocation, not the `godot` alias
flatpak run org.godotengine.Godot --headless --path . \
  --check-only --script res://autoloads/event_bus.gd   # type check — must exit 0

flatpak run org.godotengine.Godot --headless --path . \
  -s addons/gut/gut_cmdln.gd -gdir=res://tests/ -gexit  # test suite — must exit 0
```
Note: `--check-only` requires `--script` (checks one file). `-gexit` is the correct GUT flag — `-gexit_on_failure` does not exist.

**Godot class registry (TowerDefenseSequel-specific):** When a new `class_name` script is created headlessly, Godot's class registry (`.godot/global_script_class_cache.cfg`) is not automatically updated. If the test runner reports `Could not find base class "Foo"` or `Could not find type "Foo"`, add the entry manually:
```
# In .godot/global_script_class_cache.cfg, add to the list array:
{
"base": &"RefCounted",
"class": &"Foo",
"icon": "",
"is_abstract": false,
"is_tool": false,
"language": &"GDScript",
"path": "res://core/foo.gd"
}
```
Alternatively, **tell the user to open the Godot editor and save the project** (Ctrl+S) — the editor auto-populates the registry. Do this at the start of a session if new scripts were added in a prior session without an editor save.

## Step 3 — Load project context

Read source-of-truth documents before touching any code. For this project:
- `GDD.md` — game design decisions
- `TAD.md` — technical architecture decisions
- `core_plan.md` — implementation plan and GDScript rules

For other projects: look for `README.md`, `ARCHITECTURE.md`, `CLAUDE.md`, or equivalent.

## Step 4 — Implement with TDD

Follow strict red-green-refactor. **Non-negotiable:**

- One behaviour → one failing test → minimal code to pass → repeat
- Never write multiple tests before implementing
- Never implement without a failing test first
- Tests verify observable behaviour through the public interface only

For this project, additionally:
- All GDScript strictly typed — every variable, param, return type declared
- `class_name` on every script
- No bare `Array` or `Dictionary`
- No `@warning_ignore` — fix the code
- Signals named in past tense, no `Variant` in signal params

## Step 5 — Run the feedback loop

Run both commands. If either fails:
- Read the error carefully
- Fix the root cause
- Re-run until both pass
- Do **not** use `@warning_ignore` or skip checks

## Step 6 — Commit, push to dev, close issue, and update parent if applicable

```bash
git add <specific implementation files only — not progress.txt>
git commit -m "<what and why — one atomic commit>"
git push origin dev
```

One commit per issue. Do not include `progress.txt` in the commit — it is a local session file, not repo history.

**Close the issue directly:**
```bash
gh issue close <NUMBER> --comment "Implemented in commit $(git rev-parse --short HEAD) on dev. ✓"
```

**If this issue is a sub-issue**, check its body for a `> Sub-issue of #PARENT` line. If found, do both:

1. Check off the completed item in the parent's task list:
```bash
# Fetch current parent body
gh issue view <PARENT> --json body --jq '.body'

# Edit parent — replace "- [ ] #NUMBER" with "- [x] #NUMBER"
gh issue edit <PARENT> --body "<updated body with - [x] #NUMBER checked>"
```

2. Comment on the parent for the activity log:
```bash
gh issue comment <PARENT> --body "Closed sub-issue #<NUMBER> — <title> ✓"
```

Then check if all children are done:
```bash
gh issue view <PARENT> --json body --jq '.body' | grep -c '\- \[ \]'
```

If the count is 0 (no unchecked boxes remain), close the parent automatically:
```bash
gh issue close <PARENT> --comment "All sub-issues complete. Closing. ✓"
```

If any remain open, leave the parent open.

If you cannot complete: leave the issue open, note what's blocking in `progress.txt`, and explain to the user.

## Step 7 — Update progress.txt

Write (or overwrite) `progress.txt` in the project root. This is a **local file only — never committed, never git-ignored**. Delete it when the sprint is done. Keep entries concise; sacrifice grammar for brevity.

```
Issue: #<NUMBER> — <title>
Commit: <short SHA> — <commit message>
Date: <YYYY-MM-DD>

Done this session:
- <bullet per meaningful change>

Files changed:
- <path> — <why>

Decisions made:
- <non-obvious choice and reason>

Deferred / out of scope:
- <anything intentionally skipped or left partial>

Tests passing: yes / no (if no, explain)

Suggested next issue:
- #<NUMBER> — <title>  (or list open issues if unclear)

Progress: <done>/<total> issues closed under parent PRD #<PARENT> (<remaining> remaining)
```

## Step 8 — Suggest the next issue

Look at open issues and identify the best next unit of work — smallest vertical slice that builds on what was just done:

```bash
gh issue list --label ralph --state open --json number,title
```

Record the suggestion in `progress.txt` under "Suggested next issue". Do **not** create issues on behalf of the user — that is a human decision.

**Scoreboard:** If the just-completed issue has a parent PRD, count total sub-issues (open + closed) and how many are closed. Add a `Progress:` line at the bottom of `progress.txt` showing `<done>/<total> issues closed under parent PRD #<PARENT> (<remaining> remaining)`. Use:

```bash
# Count closed sub-issues that reference the parent
gh issue list --state closed --search "Sub-issue of #<PARENT>" --json number --jq 'length'
# Count open sub-issues that reference the parent
gh issue list --state open --search "Sub-issue of #<PARENT>" --json number --jq 'length'
```

If no parent exists, skip the scoreboard line.

## Step 9 — Hand off to the user

Tell the user:

> Committed and pushed to `dev`. Issue #N closed.
> `progress.txt` updated.
>
> **Suggested next issue: #M — "<title>"**
>
> **Godot (TowerDefenseSequel only):** Open the Godot editor and hit **Ctrl+S** to save — this registers any new `class_name` scripts added this session so the next session's headless tests can find them.
>
> End this session and start a fresh Claude Code instance with:
> `Read progress.txt then /implement-issue`
>
> When you're ready to ship to main: `git checkout main && git merge dev && git push origin main`
