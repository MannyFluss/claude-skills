---
name: integrate-godot-frontend-scene
description: Interview the user about how to wire a drafted Godot frontend leaf scene into the existing game/renderer. Covers placement in the scene tree, backend event binding, animation/reactivity (tweens, state transitions), and lifecycle boundaries. Use after a frontend scene has been drafted and the user wants to make it live in the game. Generates integration patches, coordinator scripts, or renderer modifications.
---

# Integrate Godot Frontend Scene

Take a self-contained drafted frontend leaf scene and wire it into the live game. This skill is the counterpart to `draft-a-godot-frontend-scene` — drafting creates the widget; this makes it react and animate.

## Invocation Flow

1. **Identify the target scene.**
   Ask: "Which drafted frontend scene are we integrating?" The user names a folder under `frontend/scenes/` or an existing scene like `bluescreen_overlay`.

2. **Interview the user on the five integration branches.**
   See [The Five Branches](#the-five-branches) below. Each branch resolves dependencies before moving to the next.

3. **Generate integration artifacts.**
   Depending on answers, produce one or more of:
   - A coordinator script (`res://scenes/frontend/coordinators/<feature>_coordinator.gd`)
   - Modifications to an existing renderer/session script (shown as a diff/patch)
   - A new parent `.tscn` that embeds the leaf scene + adds animation logic
   - Signal connection snippets

4. **Warn on scope creep.**
   If the user's plan starts adding new backend logic, new game rules, or modifying core systems, STOP and redirect: "That belongs in a backend or game design task, not frontend integration."

## The Five Branches

Walk through these in order. Do not skip branches. For each question, provide a recommended default based on existing project patterns.

### Branch 1: Placement — Where does this live in the tree?

**Q1.1: Which existing scene owns this?**
- `game_session.tscn` (top-level UI container, owns HUD, overlays, viewports)
- `game_renderer.tscn` (world renderer inside the SubViewport, Node2D)
- A new or existing sub-scene (e.g., `hud_container`, `combat_overlay`)
- A standalone coordinator that gets added dynamically

**Q1.2: Static or dynamic spawn?**
- **Static**: Embedded in a `.tscn` file, always present. Example: `bluescreen_overlay` is always in `game_session.tscn` but hidden.
- **Dynamic**: Instantiated at runtime in response to an event. Example: damage numbers spawning on hit.

**Q1.3: Is there a container/pool?**
- Single instance (one health bar per player)
- Multiple instances (enemy health bars, floating text) — needs a pool or factory pattern

**Default recommendation**: Start static in `game_session.tscn` if it's UI/HUD. Start dynamic via coordinator if it's world-space (enemy bar, floating text).

---

### Branch 2: Backend Binding — What data/events drive this?

**Q2.1: What backend signal or state change triggers updates?**
Options in this project's architecture:
- `mutation_applied` signal on `BackendInstance`
- A specific `BackendRead` query (polling)
- Direct signal from `GameState` or a subsystem
- Custom signal emitted by another frontend coordinator

**Q2.2: Which @export on the leaf scene should change?**
Map backend events to leaf scene properties:

| Backend Event | Leaf Scene @export | Transformation |
|---------------|-------------------|----------------|
| `player.hp_changed` | `current_health` | Direct assignment |
| `enemy.spawned` | `max_health` | Read from enemy data |
| `game.score_updated` | `display_value` | Format with commas |

**Q2.3: Is the data polled or pushed?**
- **Pushed**: Connect a signal. Example: `backend.mutate.mutation_applied.connect(_on_mutation)`.
- **Polled**: Read in `_process` or on a timer. Example: `_backend.read.player().health()`.

**Default recommendation**: Pushed via `mutation_applied` is the project's PHILOSOPHY #1. Only poll if the backend has no signal for that state.

---

### Branch 3: Reactivity — How does it change over time?

**Q3.1: Instant or animated transitions?**
- **Instant**: Direct assignment. `leaf.current_health = new_value`.
- **Animated**: Tween the property over time. `TweenFactory.tween_property(leaf, "current_health", old, new, 0.3)`.
- **Staged**: Multi-step. Flash red, then tween health down, then shake.

**Q3.2: What animation library/pattern?**
In this project, options are:
- `create_tween()` directly in the coordinator
- A shared `TweenFactory` or `AnimationPool` if one exists
- Custom `_process` interpolation (discouraged, but possible)
- Shader-driven animation (e.g., `entry_progress` uniform on a shader material)

**Q3.3: What triggers animation cancellation?**
- Rapid successive events (damage spam) — kill old tween, start new?
- State changes mid-animation (heal while damage tween running) — blend or snap?
- Scene removal mid-animation — clean up tween to avoid orphaned references?

**Q3.4: Does it react to layout changes?**
- Viewport resize → recalculate dynamic limits?
- Parent container resize → reflow?
- Camera zoom/position → update world-space position?

**Default recommendation**: Use `create_tween()` in the coordinator. Always kill stale tweens before starting new ones. Handle viewport resize via the existing `get_tree().root.size_changed` signal.

---

### Branch 4: Scope & Lifecycle — When does it exist?

**Q4.1: Spawn condition**
- On scene load (always there, maybe hidden)
- On game start / round start
- On specific backend event (e.g., `level_up.offered`)
- On user input (e.g., open inventory)

**Q4.2: Despawn/visibility condition**
- Never removed, only hidden/shown
- Auto-remove after animation completes (e.g., floating damage text)
- Remove on backend event (e.g., enemy dies → health bar freed)
- Remove on scene change

**Q4.3: Cleanup guarantees**
- Disconnect signals on removal?
- Free tween references?
- Return to object pool instead of `queue_free()`?

**Q4.4: Can multiple instances coexist?**
- No (singleton overlay)
- Yes, finite (2-3 buff icons)
- Yes, unbounded (floating combat text — needs pooling)

**Default recommendation**: Static for UI, dynamic with `queue_free()` for transient world elements. Always disconnect signals in `_exit_tree()`.

---

### Branch 5: Edge Cases & Interactions

**Q5.1: What happens if the backend data arrives before the frontend is ready?**
- Buffer the event and apply when ready?
- Ignore until next signal?
- Snap to current state on `_ready()`?

**Q5.2: What happens if the leaf scene is missing?**
- Crash (fail fast — acceptable in dev)
- Log error and skip (graceful degradation)
- Spawn a placeholder

**Q5.3: Does this block input or interact with other frontend?**
- Modal overlay (blocks clicks behind it)?
- Non-interactive (pure display)?
- Emits signals that OTHER coordinators consume?

**Q5.4: Should this emit its own events?**
- Signal back to backend? (Usually no — frontend observes, does not command)
- Signal to sibling coordinators? (e.g., `damage_dealt` → `combat_text_spawner`)

**Default recommendation**: On `_ready()`, snap to current backend state. Fail fast with `push_error()` if the leaf scene is missing from the expected node path. Frontend should never signal back to backend; use a coordinator-to-coordinator signal if siblings need to react.

---

## Output Artifacts

After the interview, generate one or more of these:

### A. Coordinator Script
A new `.gd` file that owns the leaf scene instance and manages its lifecycle:

```gdscript
class_name HealthBarCoordinator
extends Node

@export var leaf_scene: PackedScene
@export var target_node_path: NodePath

var _leaf: HealthBar
var _tween: Tween

func _ready() -> void:
    _leaf = leaf_scene.instantiate()
    get_node(target_node_path).add_child(_leaf)
    _sync_from_backend()
    Backend.instance.mutation_applied.connect(_on_mutation)

func _on_mutation(mutation: Mutation) -> void:
    if mutation is DamageMutation:
        _animate_health(mutation.new_hp, mutation.old_hp)

func _animate_health(new_val: float, old_val: float) -> void:
    if _tween and _tween.is_valid():
        _tween.kill()
    _tween = create_tween()
    _tween.tween_property(_leaf, "current_health", old_val, new_val, 0.3)

func _exit_tree() -> void:
    if _leaf:
        _leaf.queue_free()
```

### B. Patch / Diff
If modifying an existing scene (e.g., adding the coordinator to `game_session.tscn`):

Show the user:
```
Add to scenes/frontend/game_session.gd:
  + const HEALTH_BAR_COORDINATOR = preload("...")
  + @onready var _health_bar = HEALTH_BAR_COORDINATOR.new()

Add to scenes/frontend/game_session.tscn node tree:
  + [node name="HealthBarCoordinator" type="Node" parent="."]
  +     script = ExtResource("health_bar_coordinator")
```

### C. Signal Wiring Snippet
If the integration is just connecting existing signals:

```gdscript
# In your existing script (e.g., game_session.gd):
func _setup_health_bar() -> void:
    var bar = $HealthBar  # or instantiate dynamically
    backend.read.player().health_changed.connect(
        func(new, old): bar.current_health = new  # or tween
    )
```

---

## Scope Guardrails

**This skill is NOT for:**
- Modifying backend logic (`core/`, `Backend`, `GameState`)
- Adding new game rules or mutations
- Creating new frontend leaf scenes (use `draft-a-godot-frontend-scene`)
- Designing new backend-to-backend signals

**If the user asks for any of the above:**
> "That sounds like backend/game design work, not frontend integration. After that's implemented, come back and I'll wire the frontend to it."

---

## Quick Reference

| Concern | Default | Override When |
|---------|---------|---------------|
| Placement | Static in `game_session` | World-space or transient elements |
| Backend binding | `mutation_applied` signal | No signal exists for that state |
| Animation | `create_tween()` in coordinator | Shared tween factory exists |
| Spawn | On `_ready()` | Event-driven (level up, enemy spawn) |
| Despawn | Hide, don't remove | Transient world elements |
| Multi-instance | Singleton | Combat text, enemy bars |
| Scope | Frontend only | — |

## Example Session

**User:** Integrate the health bar I just drafted.

**Skill:** Which scene owns it — the HUD in game_session, or the world renderer?

**User:** HUD.

**Skill:** Static in the .tscn or spawned dynamically?

**User:** Static, always visible.

**Skill:** What backend data drives it?

**User:** Player health.

**Skill:** Is there a `mutation_applied` signal for damage/heal, or do we poll?

**User:** There's a `DamageMutation` and `HealMutation`.

**Skill:** Should the health drop instantly or animate down?

**User:** Animate down over 0.2s. If hit again while animating, snap to the new value and re-tween.

**Skill:** What about healing — same animation speed?

**User:** Yes.

**Skill:** Should it flash red when damage is taken?

**User:** Yes, briefly.

**Skill:** Where does that flash live — in the leaf scene or the coordinator?

**User:** Hmm... the leaf exposes `flash_intensity` as an export. Tween that.

**Skill:** Got it. What about scope — does this health bar ever go away?

**User:** No, it's always there.

**Skill:** Edge case: what if the player dies? Hide the bar or show 0?

**User:** Show 0.

**Skill:** Proposed integration:
- Add `HealthBarCoordinator` to `game_session.tscn`
- Connect `mutation_applied` → check for Damage/Heal → tween `current_health` and `flash_intensity`
- On `_ready()`, snap to current player HP
- On `_exit_tree()`, kill tween and disconnect

Confirm? [Y/n/details]

**User:** Yes.

**Skill:** → Generates `scenes/frontend/coordinators/health_bar_coordinator.gd` + patch instructions for `game_session.tscn`.
