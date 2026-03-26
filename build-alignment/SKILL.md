---
name: build-alignment
description: Structures a complex idea into a clear, walkable Markdown document for presenting to a stakeholder or collaborator. Actively solicits real artifacts (screenshots, emails, workflow examples, metrics) from the user's existing environment to ground every claim with visible evidence. Use when the user wants to present an idea to a boss or stakeholder without fumbling the explanation, wants to create a shared vision, needs to turn a well-understood idea into a document they can walk through together, or has just completed a grill-me session.
---

# Build Alignment

Turns a well-understood idea into a structured, artifact-backed Markdown document you can open with your stakeholder and walk through together — no fumbling, every claim grounded in something you can both see.

## When to use

- After `/grill-me`, when the idea is stress-tested and ready to formalize
- Before a stakeholder meeting where you need to explain a technical initiative
- When you have a clear idea but struggle to explain it to someone outside your head

## Process

### 1. Orient

Ask the user upfront:
> "Before we start — do you have artifacts ready (screenshots, emails, workflow examples, metrics)? You don't need them all now, but I'll ask for them as we go. The more concrete evidence we can embed, the stronger the document."

### 2. Interview (one question at a time)

Work through these sequentially. After each answer, ask:
> "Do you have a screenshot, file, email, or example that shows this? If so, give me the path."

Embed any artifact immediately in your working draft before moving to the next question.

**Questions:**

1. What's the idea? Describe it as if to a smart person with no context.
2. What's broken or painful today without this? Be specific.
3. Who is the stakeholder and what do they care about? (speed, cost, reliability, team health, compliance?)
4. What does success look like — concretely? How will you both know this worked?
5. What are the major phases to get there? Don't over-detail, just the big steps.
6. For each phase: what's the concrete artifact it produces? (a deployed thing, a passing test suite, a metric, a demo)
7. What are the biggest risks or unknowns? Be honest — they belong in the document.

### 3. Artifact prompting behavior

Throughout the interview, be proactive. If the user describes:
- A current broken workflow → ask for a screenshot of it
- A pattern in communication → ask for an email or Slack thread excerpt
- A metric or trend → ask for a chart or data export
- An existing tool or system → ask for a screenshot showing how it currently works

Embed artifacts inline at the point in the document where they support the claim, using:
```
![Brief description of what this shows](path/to/file.png)
```

If the user says they don't have an artifact for something, note it as:
```
> **[Evidence needed]**: A screenshot of X would strengthen this point.
```
So they can fill it in later.

### 4. Draft structure

```markdown
# [Idea Title]

## Goal
One sentence. What does the world look like when this is done?

## The Problem Today
What's broken or slow right now. Written for the stakeholder's perspective.

[artifact showing current state]

## The Idea
Clear explanation of the proposed change.

[artifact showing concept, mockup, or parallel example]

## How We Get There

### Phase 1: [Name]
What happens. What decisions get made.

**Artifact**: [What this phase produces — demo, metric, PR, test results]

[supporting artifact]

### Phase 2: [Name]
...

## How We Know It's Working
Measurable markers. Specific metrics, observable behaviors, or test results — not vibes.

## Risks & Unknowns
Honest list. Shows you've thought it through.

## Open Questions
Things the stakeholder should know exist, even if they're not being asked to resolve them.
```

### 5. Review loop

After drafting, say:
> "Here's the document. Walk through it as if you're presenting it right now — what would you change before showing this to [stakeholder name]?"

Iterate until the user confirms alignment. **Do not call it final until the user explicitly says so.**

### 6. Deliver

Output the final document as clean Markdown. Remind the user:
- Image paths are relative — the document will render correctly for anyone on the same filesystem
- Any `[Evidence needed]` blocks are gaps to fill before the meeting
- The document is meant to be read together, not handed over — open it and walk through it

## Principles

- **Evidence over assertion**: every major claim should have something visible to point at
- **No spin**: state risks honestly — the goal is shared understanding, not persuasion
- **Stakeholder language**: "Why This Matters" is written for them, not for you
- **Walkable**: the document should work as a live guide during the conversation
