---
name: draft-a-godot-frontend-scene
description: Interactively create a self-contained Godot 4.x frontend leaf scene. The user describes a visual UI/HUD/feature widget, the skill asks clarifying questions, then generates a folder under frontend/scenes/<feature>/ containing a .tscn, .gd script, and optional resources. Generated scenes are pure leaves — they never reference other frontend scenes. All configuration is exposed through @export values with validated setters. Use when the user wants to create a new visual frontend component, HUD element, UI widget, or tweakable scene.
---

# Create Godot Frontend Scene

Interactively create a self-contained, tweakable Godot 4.x frontend leaf scene.

## Invocation Flow

1. **User describes a visual feature.**
   Example: *"I want a health bar with a red fill and a text label"*

2. **Skill asks clarifying questions.**
   Walk the user through the design tree until the scene is fully specified. See [Clarifying Questions](#clarifying-questions).

3. **Skill proposes a design summary.**
   List all `@export` variables, node tree, signals, and resources. User confirms.

4. **Skill generates files.**
   Creates `frontend/scenes/<feature_name>/` with:
   - `<feature_name>.tscn`
   - `<feature_name>.gd`
   - Optional: `.gdshader`, `.tres`, texture imports

5. **If folder already exists, STOP.**
   Do not overwrite. Warn the user and show what exists. Require explicit confirmation or a new name.

## Output Structure

```
res://frontend/scenes/<feature_name>/
├── <feature_name>.tscn          # Scene file
├── <feature_name>.gd            # Script (leaf, no frontend refs)
├── <feature_name>.gdshader      # (optional) If shader needed
└── README.md                    # Auto-generated interface manifest
```

The `README.md` is an **Interface Manifest** listing every `@export`, its type, limits, default, and signals. This protects the user when they manually xref this scene into parent compositions.

## Clarifying Questions

For every feature, resolve these branches:

### 1. What nodes make up this scene?
- Godot built-ins only (`Control`, `TextureRect`, `Label`, `ProgressBar`, `ColorRect`, `CanvasLayer`, etc.)
- **Forbidden**: `AnimationPlayer`, `Tween` nodes, or sub-instances of other `frontend/scenes/*` scenes.
- Ask: "What visual elements do you see? (e.g., background bar, fill, text, icon)"

### 2. What values should be tweakable at design time?
- Every visual property the user might want to adjust → `@export`.
- Ask per element: "What about this should be adjustable? Color? Size? Text? Visibility?"
- If the user says "it should be red", ask: "Hardcoded red or @export color so you can tweak it?"

### 3. Are there dynamic limits?
- Viewport-relative? (e.g., max width = 40% of screen)
- Parent-relative? (e.g., fill = ratio of parent width)
- State-derived? (e.g., current_health clamped to max_health)
- Document the limit formula in the `##` docstring.

### 4. What state changes should emit signals?
- Any value change a parent (or Renderer) might want to react to.
- Minimum: if there are `@export` vars, there must be signals.
- Ask: "What should happen when X changes? Should the scene tell its parent?"

### 5. Are external resources needed?
- Textures, fonts, shaders from `res://assets/` → reference them.
- **Allowed**: Shared project assets.
- **Forbidden**: References to other `frontend/scenes/*` scripts or scenes.
- Ask: "Do you have an existing texture/font/shader for this, or should we use a placeholder?"

## Code Rules (Strict)

Every generated `.gd` file MUST follow these rules:

### 1. Leaf Guarantee
```gdscript
# FORBIDDEN anywhere in the file:
preload("res://frontend/scenes/")       # No references to sibling frontend scenes
get_node("../../OtherScene")            # No tree traversal to other frontend scenes
ext_resource path="res://frontend/scenes/"  # In .tscn, no frontend scene instances
```

The only references allowed are:
- Godot built-in nodes
- Resources in `res://assets/` (textures, fonts, shaders, themes)

### 2. @tool and class_name
```gdscript
@tool
class_name HealthBar
extends Control
```

### 3. Every @export has a setter + docstring
```gdscript
## Current health value.
## Limits: [0, max_health]
## Recalculates on: setter call, max_health change.
@export var current_health: float = 100.0:
    set(value):
        current_health = clampf(value, 0.0, max_health)
        _update_fill()
        if not Engine.is_editor_hint():
            health_changed.emit(current_health, value)
```

### 4. No animation logic
```gdscript
# FORBIDDEN:
create_tween()
AnimationPlayer
await get_tree().create_timer()
.tween_property()
```

Animations are the responsibility of the parent / Renderer. The scene exposes properties; something else tweens them.

### 5. Signals for all state changes
```gdscript
signal health_changed(new_value: float, old_value: float)
signal critical_state_entered()
signal layout_invalidated()
```

### 6. Safe node references
```gdscript
@onready var _fill: ColorRect = %Fill

func _update_fill() -> void:
    if not _fill:
        if Engine.is_editor_hint():
            push_warning("HealthBar: Fill node missing")
        return
    _fill.size.x = (current_health / max_health) * self.size.x
```

## Regeneration Policy

If `frontend/scenes/<feature_name>/` already exists:

1. STOP generation.
2. Read the existing `README.md` (Interface Manifest).
3. Show the user:
   ```
   ⚠️  frontend/scenes/health_bar/ already exists.
   
   Existing exports:
     - current_health: float [0, max_health]
     - max_health: float [1, 10000]
   
   Options:
   [1] Pick a new name (e.g., health_bar_v2)
   [2] Overwrite (DANGER: breaks parent scenes that embed this)
   [3] Cancel
   ```
4. Never auto-overwrite.

## Interface Manifest (README.md)

Auto-generate this in the folder:

```markdown
# HealthBar Interface Manifest

## @exports (Stable API — renaming these breaks parent scenes)
| Name | Type | Default | Limits | Description |
|------|------|---------|--------|-------------|
| current_health | float | 100.0 | [0, max_health] | Current health value |
| max_health | float | 100.0 | [1, 10000] | Maximum health |
| fill_color | Color | Color.RED | alpha [0,1] | Color of the health fill |

## Signals
| Name | Payload | When |
|------|---------|------|
| health_changed | (new, old) | When current_health changes |
| critical_state_entered | () | When current_health < 25% of max |

## Node Tree
- HealthBar (Control)
  - Background (ColorRect)
  - Fill (ColorRect)
  - Label (Label)

## Resources
- None (or list textures/fonts used from res://assets/)

## Parent Scenes
- None tracked. If you embed this in a .tscn, document it here manually.
```

## Quick Reference

| Rule | Enforcement |
|------|-------------|
| Leaf guarantee | No `frontend/scenes/*` references in .gd or .tscn |
| `@tool` | Mandatory first line |
| `class_name` | Mandatory, PascalCase, matches folder name |
| `@export` setter | Must clamp/validate; must have `##` docstring |
| `@export` default | Must be sane and within limits |
| Animation | **Forbidden** — pure state only |
| Signals | Required if `@export` vars exist |
| Node refs | Safe (`@onready` + null check) |
| Regeneration | Stop and warn if folder exists |

## Example Session

**User:** Create a health bar.

**Skill:** What visual elements should it have?

**User:** A background, a red fill, and a text label showing the number.

**Skill:** Should the color be hardcoded red or an @export so you can tweak it?

**User:** Export it.

**Skill:** What about the text — should it show "100/100" or just "100"?

**User:** Just the current value.

**Skill:** Should the bar width be a fixed pixel size or a ratio of screen width?

**User:** Ratio of screen width, max 40%.

**Skill:** Should it emit a signal when health drops below 25%?

**User:** Yes.

**Skill:** Proposed design:
- Exports: `current_health`, `max_health`, `screen_width_ratio`, `fill_color`, `text_color`
- Limits: screen_width_ratio clamped to [0.0, 0.4] via viewport
- Signals: `health_changed(new, old)`, `critical_state_entered()`
- Nodes: Control → Background (ColorRect), Fill (ColorRect), Label (Label)

Confirm? [Y/n]

**User:** Yes.

**Skill:** → Generates `frontend/scenes/health_bar/health_bar.tscn`, `health_bar.gd`, `README.md`
