---
name: decompose-issue
description: Break a large GitHub issue into atomic ralph-sized sub-issues (one behaviour, one session each). Use when an issue is too big to implement in one go, when implement-issue flags it as oversized, or when you want to split an epic into a story queue.
---

# Decompose Issue

Break one fat issue into a queue of atomic stories, each small enough for a single `/implement-issue` session.

## Step 1 — Read the issue

```bash
gh issue view <NUMBER> --json title,body
```

Also read `progress.txt` if it exists — prior context may clarify scope.

## Step 2 — Explore the codebase for scope

Before proposing a split, understand what the issue actually touches. Read relevant files, check existing tests, look at related issues:

```bash
gh issue list --label ralph --state open --json number,title
```

## Step 3 — Propose the split

Present a numbered list of proposed sub-issues. Each one must have:
- A single, unambiguous acceptance condition ("done" is obvious)
- Changes confined to one area of the codebase
- No hidden dependency on another sub-issue being done first (or explicitly sequenced if there is one)

Format:
```
Proposed split of #N — <original title>:

1. <sub-title> — <one-line acceptance condition>
2. <sub-title> — <one-line acceptance condition>
3. <sub-title> — <one-line acceptance condition>

Suggested order: 1 → 2 → 3 (reason: <dependency or risk rationale>)
```

Ask the user: "Does this split look right? Any changes before I create the issues?"

## Step 4 — Create sub-issues on confirmation

Only after the user approves the split. Create each child with a consistent header so the tree is traceable:

```bash
gh issue create \
  --title "<sub-title>" \
  --body "> Sub-issue of #<PARENT>\n\n## Acceptance criteria\n<condition>\n\n## Context\n<anything the implementer needs to know>" \
  --label ralph
```

Capture each new issue number as it's created — you need them for Step 5.

## Step 5 — Update the parent with a task checklist

After all children are created, edit the parent issue body to append a progress checklist. This makes the tree visible from the top and GitHub renders it as a progress bar:

```bash
# Get current body first
gh issue view <PARENT> --json body

# Then edit — append the checklist to the existing body
gh issue edit <PARENT> --body "<existing body>

## Sub-issues
- [ ] #A — <sub-title>
- [ ] #B — <sub-title>
- [ ] #C — <sub-title>"
```

If the parent was just a planning placeholder with no real body, replace the body entirely with the checklist. If it's a real deliverable, append after the existing content.

Do **not** close the parent — leave it open so it tracks overall progress as children close.

## Step 6 — Hand off

Tell the user:

> Decomposed #N into: #A — "<title>", #B — "<title>", #C — "<title>"
>
> Start with: `Read progress.txt then implement issue #A`
