# Example: Finished Build Alignment Document

This shows how a completed document looks with artifacts woven in.

---

# Unified Deployment Pipeline

## Goal
Every service deploys through a single, observable pipeline — no manual steps, no tribal knowledge required.

## The Problem Today
Right now deployments are handled differently per team. Some use scripts in personal repos, some use the shared Jenkins job (which nobody fully understands), and hotfixes go out via SSH by whoever is on call. When something breaks mid-deploy, there's no consistent way to know what state things are in.

![Current deployment board showing 4 different deploy methods across services](/home/manny/projects/screenshots/deploy-chaos.png)

This came up directly in the Q3 incident retro — 3 of 5 incidents had "unclear deploy state" as a contributing factor.

![Excerpt from Q3 retro doc highlighting deploy confusion as a recurring theme](/home/manny/projects/screenshots/q3-retro-excerpt.png)

## The Idea
Consolidate all service deployments under a single pipeline with a standard interface. Each service declares its deploy config in a `deploy.yaml` at its root. The pipeline handles the rest: staging promotion, smoke tests, rollback triggers, and a shared dashboard showing live deploy state.

![Draft of the deploy.yaml schema we've been discussing](/home/manny/projects/infra/docs/deploy-schema-draft.png)

## How We Get There

### Phase 1: Standardize one service
Pick the least-critical service and migrate it fully. Shake out the schema, the rollback logic, and the dashboard integration.

**Artifact**: One service deploying end-to-end through the new pipeline, with a working rollback demonstrated in staging.

![The notifications service — a good candidate, low traffic, well-isolated](/home/manny/projects/screenshots/notifications-service-overview.png)

### Phase 2: Migrate remaining services
Roll out to all services one at a time. Each migration is a PR — reviewable, reversible.

**Artifact**: All services listed in the dashboard. Old deploy scripts archived.

### Phase 3: Retire legacy paths
Remove the old Jenkins job and SSH deploy scripts. Update the runbook.

**Artifact**: Updated runbook, no remaining references to the old process in the incident response docs.

> **[Evidence needed]**: A screenshot of the current Jenkins job config would strengthen the case for why it needs to go.

## How We Know It's Working
- Zero deployments outside the pipeline 30 days after Phase 3
- Mean time to deploy drops from ~40 min (current average) to under 15 min
- On-call engineers can answer "what is currently deployed where" without Slack-ing anyone

## Risks & Unknowns
- The payments service has unusual deploy requirements (PCI compliance step). May need a plugin hook rather than a standard config.
- We don't yet know how this interacts with the database migration step in the auth service.
- Rollback logic for stateful services (anything with a DB migration) needs more design work before Phase 2.

## Open Questions
- Do we want the dashboard to be part of the existing ops portal or stand-alone?
- Who owns the pipeline going forward — platform team or each service team?
