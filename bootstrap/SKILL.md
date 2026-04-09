---
name: bootstrap
description: Review conversation context to create a bootstrap script or install guide for a program or process the user just set up. Use when user says "bootstrap this", "create a setup script", "document what I just did", or wants to capture a setup for future reinstalls.
---

# Bootstrap

## Workflow

1. **Review context** — read the current conversation to extract:
   - What was installed (packages, tools, configs)
   - What commands were run (in order)
   - Any config files created or modified
   - Environment variables or secrets needed

2. **Draft the bootstrap** — write a file to the current working directory:
   - Use a descriptive filename: `setup-<thing>.sh` or `setup-<thing>.md`
   - Shell script if the steps are fully automatable
   - Markdown guide if manual steps, decisions, or credentials are involved
   - Use `#!/usr/bin/env bash` and `set -e` for scripts
   - Add `# --- Section Name ---` comments to group steps
   - Annotate non-obvious commands with inline comments
   - Note any secrets/env vars needed but don't hardcode values

3. **Ask about dotfiles integration** — after writing the file, ask the user:
   - Should this be added to `~/.dotfiles`?
   - Based on what it is, suggest the right place:
     - Reusable utility script → `~/.dotfiles/bin/`
     - One-off install script → `~/.dotfiles/post-install-scriptlets/`
     - Config file → run `dotfile-add <file>`
     - New package → append to `~/.dotfiles/packages/dnf-packages.txt` or `flatpak-apps.txt`
   - If the user says yes, make the change and remind them to run `cloud-upload` to commit and push
