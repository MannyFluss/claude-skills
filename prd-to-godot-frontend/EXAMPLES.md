# Examples: Good and Bad Frontend Patterns

Real examples from the TowerDefenseSequel codebase, annotated with what to emulate and what to avoid.

---

## Good Example 1: `AlphabetCounter` (`assets/scenes/AlphabetCounter/alphabet_counter.gd`)

```gdscript
@tool
extends Node2D

const SYMBOLS: Array[String] = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z",
    "!", "?", "!?", "!!!",
]

@export var value: int = 0:
    set(v):
        var n := SYMBOLS.size()
        value = ((v % n) + n) % n
        _update_label()

@onready var _label: RichTextLabel = %RichTextLabel

func _ready() -> void:
    _update_label()

func map(from_min: float, from_max: float, z: float) -> void:
    var clamped := clampf(z, from_min, from_max)
    var remapped := remap(clamped, from_min, from_max, 0.0, float(SYMBOLS.size() - 1))
    value = round(remapped)

func _update_label() -> void:
    if _label:
        _label.text = SYMBOLS[value]
```

### Why it's good
- `@tool` is present — editor-time validation works.
- `@export` has a setter with explicit clamping logic (`((v % n) + n) % n` wraps within the valid symbol range).
- Safe null check on `_label` before updating.
- No tween or animation logic — pure state + reactive update.

### What could be improved per this skill
- Missing `class_name` for type safety and testability.
- Missing docstring comment on `@export var value` specifying limits and recalculation triggers.
- Missing signal emission when `value` changes (if a Renderer might want to animate the label).

---

## Good Example 2: `Basic` (`assets/scenes/Basic/basic.gd`)

```gdscript
@tool
extends Node2D

@onready var mmi: MultiMeshInstance2D = $MultiMeshInstance2D

func _ready() -> void:
    var mm := mmi.multimesh
    for i in mm.instance_count:
        var col := i % 2
        var row := i / 2
        var pos := Vector2(col * 120.0, row * 120.0)
        mm.set_instance_transform_2d(i, Transform2D(0.0, pos))
```

### Why it's good
- `@tool` present.
- Simple, deterministic editor-time setup.

### What could be improved per this skill
- Missing `class_name`.
- Hardcoded `120.0` spacing could be an `@export` with setter validation.
- No signals (may not be needed for this specific scene, but good to consider).

---

## Bad Example 1: `BluescreenOverlay` (`scenes/frontend/bluescreen_overlay.gd`)

This is the project's **existing** bluescreen overlay. It violates several rules of this skill.

### Violation: Animation Logic Inside Frontend

```gdscript
@export var entry_trans: Tween.TransitionType = Tween.TRANS_QUAD
@export var entry_ease: Tween.EaseType = Tween.EASE_IN_OUT

var _entry_tween: Tween = null

func show_offer(offer: LevelUpOffer) -> void:
    # ...
    if _entry_tween != null and _entry_tween.is_valid():
        _entry_tween.kill()
    _entry_tween = create_tween()
    _entry_tween.set_trans(entry_trans)
    _entry_tween.set_ease(entry_ease)
    _entry_tween.tween_method(_set_entry_progress, 0.0, 1.0, duration_sec)
    # ...
```

**Why it's bad**: The frontend scene owns tween creation and interpolation logic. Per this skill, the frontend should expose `entry_progress` as an `@export` with a setter that updates the shader uniform, and emit a signal like `offer_shown(offer)`. The Game Renderer should own the tween.

### Violation: Missing `@tool`

The script lacks `@tool` at the top. This means no editor-time validation or visual preview of the overlay styling.

### Violation: Missing `class_name`

While the file does define `class_name BluescreenOverlay`, many other frontend scenes in the project do not. This one gets it right, but the pattern is inconsistent.

### Violation: No Setter Validation on Exports

```gdscript
@export var title_font_size: int = 24
@export var choice_font_size: int = 18
@export var skip_font_size: int = 20
@export var skip_button_min_height: float = 44.0
@export var choice_button_min_size: Vector2 = Vector2(200.0, 80.0)
@export var card_container_separation: int = 12
```

These `@export` variables have **no setters**. Changing them in the Inspector at runtime or in the editor does not trigger any reactive update. The scene must be re-instantiated or manually refreshed.

### Violation: No Signals for State Changes

`show_offer()` and `hide_offer()` mutate internal state (visibility, shader parameters, card contents) but emit no signals. A Renderer cannot observe these transitions to chain animations or sound effects.

### Violation: Hardcoded Pixel Values

```gdscript
offset_left = -540.0
offset_top = -360.0
offset_right = 540.0
offset_bottom = 360.0
```

In the `.tscn`, the `CardsContainer` uses hardcoded pixel offsets. These should be dynamic or `@export`-driven with viewport-relative limits.

---

## Good Example 3: GUT Test (`tests/test_bluescreen_overlay.gd`)

```gdscript
class_name TestBluescreenOverlay
extends GutTest

const OVERLAY_SCENE: PackedScene = preload("res://scenes/frontend/bluescreen_overlay.tscn")

var _overlay: BluescreenOverlay
var _backend: BackendInstance

func before_each() -> void:
    _backend = Backend.create_fresh(0)
    var inst: Node = OVERLAY_SCENE.instantiate()
    _overlay = inst as BluescreenOverlay
    add_child_autofree(_overlay)
    _overlay.setup(_backend)

func test_tear_intensity_zero_at_full_hp() -> void:
    var intensity: float = _overlay._compute_tear_intensity(100, 100)
    assert_eq(intensity, 0.0)

func test_tear_intensity_clamps_to_one() -> void:
    var intensity: float = _overlay._compute_tear_intensity(-10, 100)
    assert_eq(intensity, 1.0)

func test_show_offer_starts_entry_progress_at_zero() -> void:
    _backend.mutate.request(OfferLevelUpRequest.new(&"pointer"))
    var offer: LevelUpOffer = _backend.read.level_ups().pending()
    _overlay.show_offer(offer)
    var mat: ShaderMaterial = _overlay._shader_material
    var progress: float = mat.get_shader_parameter("entry_progress")
    assert_eq(progress, 0.0)
```

### Why it's good
- Uses `class_name` on the test class.
- Uses `add_child_autofree` for cleanup.
- Tests clamp behavior (`_compute_tear_intensity` clamps correctly).
- Tests state after method calls (`show_offer` sets progress to 0).
- Uses backend integration for realistic setup.

### What could be improved per this skill
- Tests should also assert signal emissions (e.g., `watch_signals(_overlay)` and check for `offer_shown`).
- Missing overflow/clamp tests for `@export` variables (the overlay doesn't have setters, so this isn't testable — which is the root problem).
- Missing tool-safety tests (`Engine.is_editor_hint()` behavior).

---

## Summary Table

| Pattern | Good Example | Bad Example | Rule |
|---------|-------------|-------------|------|
| `@tool` | `AlphabetCounter` | `BluescreenOverlay` | Mandatory first line |
| `class_name` | `AlphabetCounter` (almost), tests | Many frontend scenes | Mandatory, PascalCase |
| `@export` setter with validation | `AlphabetCounter.value` | `BluescreenOverlay` font sizes | Must clamp/validate |
| No tween logic in frontend | `AlphabetCounter` | `BluescreenOverlay.show_offer` | Forbidden |
| Signals for state changes | (Not shown in good exs) | `BluescreenOverlay` | Must emit on change |
| Dynamic limits | (Not shown in good exs) | `BluescreenOverlay` hardcoded offsets | Must be viewport/parent relative |
| GUT tests | `test_bluescreen_overlay.gd` | (Missing for many scenes) | Must cover overflow, signals, tool safety |
