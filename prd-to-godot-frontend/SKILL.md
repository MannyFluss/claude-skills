---
name: prd-to-godot-frontend
description: Convert Product Requirements Documents (PRDs) into discrete, red-green testable GitHub issues for Godot 4.x frontend development. Each issue produces a self-contained, independently verifiable Godot scene adhering to strict contractual boundaries with the Game Renderer. Use when converting a PRD into frontend implementation issues, creating Godot UI widget tickets, or when user mentions Godot frontend scenes, HUD elements, UI widgets, or export setter contracts.
---

# PRD to Godot Frontend Issues

Convert PRDs into discrete, red-green testable GitHub issues for Godot 4.x frontend deliverable scenes (UI widgets, HUD elements, visual assets). Excludes coordinator/orchestrator scenes like GameSession that inherently handle cross-cutting concerns.

## Quick start

1. Receive a PRD (or PRD excerpt).
2. Decompose into atomic/composite scene issues.
3. For each issue, generate the structured template below.
4. End with a Renderer Integration Prompt for user decision.

## Issue Structure Template

Every generated issue must follow this exact structure:

```markdown
## Objective
[One sentence: what scene file and script this issue creates]

## Acceptance Criteria (Red → Green)
- [ ] **RED**: Write `test_[scene_name].gd` using GUT that asserts [specific behavior]. Running it fails.
- [ ] **GREEN**: Implement `[scene_name].gd` and `[scene_name].tscn` such that the test passes.
- [ ] **REFACTOR**: Ensure all `@export` setters have explicit validation and `@tool` behavior works in editor.

## Deliverables
1. `res://frontend/[category]/[scene_name].tscn`
2. `res://frontend/[category]/[scene_name].gd`
3. `res://frontend/[category]/tests/unit/test_[scene_name].gd` (GUT unit test)
4. `res://frontend/[category]/tests/visual/test_[scene_name].tscn` (visual verification scene)

## Script Specification
- `@tool` — must be first line.
- `class_name [PascalCaseName]` — for type safety and testability.
- Every `@export` must have a setter with clamp/validation and a docstring comment specifying physical meaning, hard min/max (or dynamic formula), and what triggers recalculation.
- Signals must be emitted for all state changes the Renderer might animate.

## Forbidden Patterns
- `Tween`, `AnimationPlayer`, or interpolation logic.
- `await get_tree().create_timer()` for visual delays.
- Direct modification of `position`, `scale`, `modulate`, or `size` outside of setter-driven reactive updates.
- Hardcoded pixel values that should be dynamic.

## GUT Unit Test Requirements
- Overflow & clamp tests for every `@export` numeric variable.
- Signal emission tests (correct payload, idempotency).
- State consistency tests (rapid successive setter calls, null-safety).
- Tool script safety tests (`Engine.is_editor_hint()` behavior).

## Visual Test Scene Requirements
- Instantiate target scene at readable size, centered.
- Debug panel showing real-time `@export` values.
- Interactive controls (`HSlider`, `SpinBox`, `Button`) for every `@export`.
- Viewport resize preset buttons (e.g., 1920x1080, 1280x720, 800x480).
- PASS/FAIL indicator or manual checklist label.

## Renderer Integration Prompt
Once verified, the scene exposes this contract to the Game Renderer. Suggest a follow-up issue for the user to review and decide whether to spawn.
```

## Scope

This skill applies to **deliverable frontend scenes** — self-contained visual assets that the Game Renderer instantiates and animates:
- UI widgets (health bars, stat icons, progress fills)
- HUD elements (score counters, minimaps, ability buttons)
- Visual effects (particle containers, shader-driven overlays)
- Menu components (choice cards, sliders, toggles)

It does **not** apply to coordinator/orchestrator scenes (e.g., `GameSession`) that manage backend binding, scene tree assembly, or cross-cutting concerns. Those follow their own architectural rules.

## Decomposition Rules

- **Atomic scenes**: A simple widget (progress fill, stat icon) → one issue.
- **Composite scenes**: A complex widget with tightly coupled internal parts (health bar + embedded label sharing layout logic) → one issue IF sub-parts are not reusable. If reusable (e.g., generic `BarFill`), split into separate issues.
- **Interaction logic**: Lives in the frontend scene; the *consequence* (e.g., "slide to X") is signaled, not executed via tween.

**Decision heuristic**: If a sub-component can be instantiated alone, rendered sensibly, and tested without its parent, it deserves its own issue.

## Agent Execution Guidelines

When an agent picks up one of these issues:

1. Read the PRD chunk associated with the issue.
2. Write the RED GUT test first. The test must fail meaningfully.
3. Implement the scene with `@tool`, `class_name`, all `@export` setters with limits, and signal emissions.
4. Run the GUT tests and verify all pass.
5. Build the visual test scene with sliders, debug labels, viewport presets, and PASS/FAIL indicators.
6. Do NOT add tween/animation logic. Add a comment: `# Animation handled by Renderer via tweening [property_name]`.
7. Submit the scene + GUT tests + visual test scene + integration prompt.

## Verification Checklist

Before marking a frontend issue complete:
- [ ] All `@export` vars have setters with documented limits.
- [ ] `@tool` script runs without errors in the editor.
- [ ] GUT tests pass: overflow/clamp, signals, consistency, tool safety.
- [ ] Visual test scene displays correctly with all interactive controls functional.
- [ ] Dynamic limits correctly recalculate on viewport resize presets in the visual scene.
- [ ] No `Tween`, `AnimationPlayer`, or `create_timer` exists in the script.
- [ ] Signals are emitted for all state changes.
- [ ] Renderer Integration Prompt is generated and linked for user decision.

## Quick Reference

| Concept | Rule |
|---------|------|
| `@tool` | Mandatory first line |
| `class_name` | Mandatory, PascalCase, matches scene purpose |
| `@export` setter | Must clamp/validate; must document limits in comment |
| Dynamic limits | Re-query viewport/parent on setter call and resize events |
| Animation | **Forbidden** in frontend. Use signals + exposed properties |
| GUT tests | Must cover overflow, signals, consistency, tool safety |
| Visual test scene | Must include sliders, debug panel, viewport presets, PASS/FAIL |
| Integration | Generate a suggested prompt; user decides follow-up issue |

## References

- [REFERENCE.md](REFERENCE.md) — Detailed templates, dynamic limit patterns, forbidden/good examples.
- [EXAMPLES.md](EXAMPLES.md) — Real project examples (good and bad) from the TowerDefenseSequel codebase.
- [scripts/validate_frontend.py](scripts/validate_frontend.py) — Standalone CLI script to validate a `.gd` file.
- **GUT Contract Test Suite** — Copy `tests/frontend/test_frontend_contract.gd` into the target project. Subclass it per scene to enforce rules at test time:
  ```gdscript
  class_name TestMyWidgetContract
  extends TestFrontendContract

  func before_each() -> void:
      script_path = "res://frontend/hud/my_widget.gd"
      super.before_each()
  ```
