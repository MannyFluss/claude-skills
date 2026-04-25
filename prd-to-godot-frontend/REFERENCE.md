# Reference: PRD to Godot Frontend Issues

Detailed templates, patterns, and rules for generating frontend issues from PRDs.

---

## 1. Issue Structure Template (Full)

```markdown
## Objective
Create `res://frontend/[category]/[scene_name].tscn` + `[scene_name].gd` — [one sentence description].

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

### Required Annotations
- `@tool` — must be first line.
- `class_name [PascalCaseName]` — for type safety and testability.

### Export Variable Contract
Every `@export` must follow this pattern:

```gdscript
@export var max_health: float = 100.0:
    set(value):
        max_health = clampf(value, 1.0, 10000.0)
        _update_health_bar()
```

**Dynamic Limits Pattern** (when bounds depend on viewport or siblings):

```gdscript
@export var bar_width_ratio: float = 0.5:
    set(value):
        var screen_w = get_viewport_rect().size.x if Engine.is_editor_hint() else DisplayServer.window_get_size().x
        bar_width_ratio = clampf(value, 0.0, 1.0)
        _update_geometry()
```

**Explicit Limit Documentation**:
Every `@export` must have a docstring comment specifying:
- Physical meaning
- Hard min/max (or formula for dynamic min/max)
- What triggers recalculation

Example:
```gdscript
## Horizontal offset from screen center, in pixels.
## Limits: [-screen_width/2, +screen_width/2]
## Recalculates on: viewport resize, setter call.
@export var x_offset: float = 0.0:
    set(value):
        var limit = get_viewport_rect().size.x / 2.0
        x_offset = clampf(value, -limit, limit)
        position.x = x_offset
```

### Signal Contract
The scene must emit signals for any state change the Renderer might want to animate or react to:

```gdscript
signal value_changed(new_value: float, old_value: float)
signal layout_invalidated()  # When dynamic limits shift due to resize
signal interaction_triggered(type: String, payload: Dictionary)
```

### Forbidden Patterns
The following are **explicitly forbidden** in frontend scene scripts:
- `Tween`, `AnimationPlayer`, or interpolation logic.
- `await get_tree().create_timer()` for visual delays.
- Direct modification of `position`, `scale`, `modulate`, or `size` outside of setter-driven reactive updates.
- Hardcoded pixel values that should be dynamic (e.g., `position.x = 100` instead of `position.x = x_offset`).

## GUT Unit Test Requirements
The `test_[scene_name].gd` must use the Godot Unit Test (GUT) addon and cover the following:

### Overflow & Clamp Tests
For every `@export` numeric variable:
- Assert that setting a value above the maximum limit clamps to the max.
- Assert that setting a value below the minimum limit clamps to the min.
- Assert that dynamic limits (viewport-relative, parent-relative, sibling-relative) correctly constrain the value after simulated resize or tree changes.
- Assert that `Vector2`/`Vector3` components are clamped per-component when limits are axis-dependent.

### Signal Emission Tests
- Assert that changing an `@export` value emits the correct signal with the correct payload (`new_value`, `old_value`).
- Assert that boundary transitions (e.g., crossing a critical threshold) emit the correct state-change signals.
- Assert that no signals are emitted when a setter receives a value that results in no actual change (idempotency).

### State Consistency Tests
- Assert that the visual/internal state remains consistent after rapid successive setter calls (stress test).
- Assert that all `@export` defaults are sane and within limits at `_ready()` time.
- Assert that the scene does not crash or error when child nodes referenced by setters are temporarily missing (null-safety).

### Tool Script Safety Tests
- Assert that `_ready()` and setter logic behave correctly when `Engine.is_editor_hint()` is true (no game-side side effects in editor).
- Assert that `push_warning` is emitted (where applicable) when expected child nodes are missing.

### Example GUT Test Skeleton
```gdscript
extends GutTest

var scene: HealthBar

func before_each():
    scene = HealthBar.new()
    add_child_autofree(scene)

func test_current_health_clamps_to_max():
    scene.max_health = 100.0
    scene.current_health = 200.0
    assert_eq(scene.current_health, 100.0, "Should clamp to max_health")

func test_current_health_clamps_to_min():
    scene.current_health = -50.0
    assert_eq(scene.current_health, 0.0, "Should clamp to 0")

func test_emits_value_changed():
    scene.max_health = 100.0
    scene.current_health = 50.0
    watch_signals(scene)
    scene.current_health = 30.0
    assert_signal_emitted_with_parameters(scene, "value_changed", [30.0, 50.0])

func test_dynamic_limit_respects_viewport():
    var vw = 1920.0
    # Simulate viewport size if necessary via mocking or tree setup
    scene.screen_width_ratio = 0.9
    assert_lte(scene.screen_width_ratio, 0.4, "Should respect viewport max of 40%")
```

## Visual Test Scene Requirements
The `test_[scene_name].tscn` is the final product the user reviews. It must:

1. **Instantiate the target scene** at a readable size in the center of the test viewport.
2. **Include a debug panel** (e.g., a `VBoxContainer` of `Label` or `RichTextLabel` nodes) showing real-time values of all `@export` variables.
3. **Include interactive controls** (e.g., `HSlider`, `SpinBox`, `Button`) for every `@export` variable so the user can mutate values at runtime and observe setter constraints in action.
4. **Include viewport resize presets** (e.g., buttons for 1920x1080, 1280x720, 800x480) to verify that dynamic limits recalculate correctly and the scene remains visually correct.
5. **Display a PASS/FAIL indicator** that runs the associated GUT test suite inline or loads its results. At minimum, the visual scene must have a `Label` that shows the result of a manual checklist:
   - All exports clamp correctly when sliders are pushed beyond limits.
   - Signals fire and are visible in the debug panel.
   - Scene does not error when child nodes are temporarily hidden/removed.
   - Layout remains valid across all viewport presets.

### Visual Test Scene Script Skeleton
```gdscript
extends Control

@onready var target = $HealthBar
@onready var debug_label = $DebugPanel/Values
@onready var pass_fail_label = $PassFailIndicator

func _ready():
    _connect_sliders()
    _update_debug()
    target.value_changed.connect(_on_value_changed)

func _connect_sliders():
    $Controls/HealthSlider.value_changed.connect(func(v): target.current_health = v)
    $Controls/MaxHealthSlider.value_changed.connect(func(v): target.max_health = v)
    # etc for all exports

func _update_debug():
    debug_label.text = "current_health: %s\nmax_health: %s\nscreen_ratio: %s" % [
        target.current_health, target.max_health, target.screen_width_ratio
    ]

func _on_value_changed(new, old):
    _update_debug()
    # Optionally flash the PASS/FAIL label green briefly
```

## Renderer Integration Prompt
Once this issue is verified, the scene exposes this contract to the Game Renderer. The following is a **suggested follow-up** for the user to review and decide whether to spawn as a new issue:

| Property | Type | Animator Friendly | Notes |
|----------|------|-------------------|-------|
| `current_health` | `float` | Yes | Tween this for damage/heal animations |
| `x_offset` | `float` | Yes | Tween this for slide-in/out |
| `is_highlighted` | `bool` | No | Use `modulate` tween on renderer side instead |

| Signal | Payload | Renderer Action |
|--------|---------|-----------------|
| `value_changed` | `(new, old)` | Trigger tween from `old` to `new` |
| `interaction_triggered` | `(type, dict)` | Route to game state machine |

**Suggested Follow-up Issue (user decides whether to create):**
```markdown
## Objective
Integrate `[scene_name]` into the Game Renderer at `[insert location]`.

## Integration Steps
- [ ] Instantiate `[scene_name]` in renderer scene tree at `[node_path]`.
- [ ] Connect `value_changed` to Renderer's tween factory: `TweenFactory.tween_property(scene, "current_health", old, new, duration)`.
- [ ] Connect `interaction_triggered` to `[input_router/state_machine]`.
- [ ] Ensure viewport resize signals propagate to scene's dynamic limit recalculation.
- [ ] Verify no frontend scene logic was modified during integration (black-box test).
```
```

---

## 2. Setter Validation Rules (Strict)

For every `@export` of type `int`, `float`, `Vector2`, `Vector2i`, `Vector3`, `Color`, or `String`:

### Numbers (`int`, `float`, `Vector2`, `Vector3`)
- Must specify `min`, `max`, or a dynamic limit formula.
- If the limit is dynamic (screen size, parent size), the setter must call a `_recalculate_limits()` or similar that re-queries the context.
- `Vector2`/`Vector3` components must be clamped per-component if limits are axis-dependent.

### Colors (`Color`)
- Must specify whether alpha is clamped (usually `[0, 1]`).
- If the color represents a game state (e.g., "low health red"), the setter should validate against a palette enum or call `_validate_palette()`.

### Strings (`String`)
- If the string represents a key (texture path, translation key), setter must validate existence via `ResourceLoader.exists()` or a registry check.
- If the string represents a display value, length limits must be enforced.

### Booleans (`bool`)
- Booleans are exempt from range limits but must trigger side-effect updates (e.g., `visible = is_enabled`).

---

## 3. Dynamic Limit Patterns

### Viewport-Relative
```gdscript
@export var margin_left: float = 0.0:
    set(value):
        var vw = get_viewport_rect().size.x
        margin_left = clampf(value, 0.0, vw * 0.5)
        _update_margins()
```

### Parent-Relative
```gdscript
@export var fill_ratio: float = 0.0:
    set(value):
        if get_parent() is Control:
            var max_w = get_parent().size.x
            fill_ratio = clampf(value, 0.0, 1.0)
            custom_minimum_size.x = max_w * fill_ratio
```

### Sibling-Dependent
```gdscript
@export var label_padding: float = 10.0:
    set(value):
        var sibling_label = get_node_or_null("../Label")
        var max_pad = sibling_label.size.x if sibling_label else 100.0
        label_padding = clampf(value, 0.0, max_pad)
```

---

## 4. Tool Script Requirements

Because every script is `@tool`:
- `_ready()` must check `Engine.is_editor_hint()` to avoid executing game-logic side effects in the editor.
- Setters must work in editor mode (this is how visual verification happens before runtime).
- If a node requires a child node reference (e.g., `$TextureRect`), the setter must use `@onready` or safe-path resolution and emit a warning in the editor if the node is missing.

```gdscript
@tool
class_name HealthBar
extends Control

@export var current_health: float = 100.0:
    set(value):
        current_health = clampf(value, 0.0, max_health)
        _update_fill()
        if not Engine.is_editor_hint():
            value_changed.emit(current_health, value)  # Note: emit old/new correctly

func _update_fill():
    var fill = get_node_or_null("Fill")
    if not fill:
        if Engine.is_editor_hint():
            push_warning("HealthBar: Fill node missing")
        return
    fill.size.x = (current_health / max_health) * self.size.x
```

---

## 5. Example: PRD to Issues

**PRD Excerpt:**
> "The player HUD shall display a health bar that depletes when damage is taken. The bar should be anchored to the bottom-left with a 20px margin, not exceeding 40% of screen width. When health drops below 25%, the bar should flash red."

**Decomposition Decision:**
The health bar is a single composite widget (fill + background + optional label) where the internal parts share layout logic. Kept as one issue. If the "BarFill" pattern is reused elsewhere in the PRD, a separate generic `BarFill` issue should be extracted first.

**Generated Issue:**

### Issue 1: `HealthBar` Scene
- **Objective**: Create `res://frontend/hud/health_bar.tscn` + `health_bar.gd`
- **Exports**: `current_health`, `max_health`, `screen_width_ratio`, `bottom_margin`, `critical_threshold`
- **Limits**: `screen_width_ratio` clamped to `[0.0, 0.4]` relative to viewport; `bottom_margin` clamped to `[0, viewport_height/2]`; `critical_threshold` clamped to `[0.0, max_health]`.
- **Signals**: `health_changed(new, old)`, `critical_state_entered()`, `critical_state_exited()`
- **Forbidden**: No flashing/tween logic. The `modulate` property is exposed for the Renderer to tween.
- **GUT Tests**: Overflow on all numeric exports; signal emission on health change and threshold crossing; dynamic limit recalculation on viewport resize; no crash when `Fill` node is missing.
- **Visual Test Scene**: Sliders for health/max_health/screen_ratio/bottom_margin; debug panel showing live values; viewport preset buttons (1080p, 720p, mobile); PASS/FAIL label driven by manual checklist.
- **Integration Prompt**: Renderer will tween `modulate` to `Color.RED` and back on `critical_state_entered/exited`.

---

## 6. GUT Contract Test Suite

Instead of (or in addition to) the Python CLI validator, you can enforce the skill rules **inside the GUT test suite itself**.

### Base Class: `TestFrontendContract`

Place this in your project's test directory (e.g., `tests/frontend/test_frontend_contract.gd`):

```gdscript
class_name TestFrontendContract
extends GutTest

# Meta-test suite that validates a frontend GDScript scene against the
# prd-to-godot-frontend skill rules.  Subclass this and set `script_path`
# in `before_each()`.

var script_path: String = ""
var _source: String = ""
var _lines: PackedStringArray = []

func before_each() -> void:
    if script_path.is_empty():
        push_warning("TestFrontendContract: script_path is empty")
        return
    var file := FileAccess.open(script_path, FileAccess.READ)
    assert_not_null(file, "Could not open script: %s" % script_path)
    _source = file.get_as_text()
    _lines = _source.split("\n")

func test_tool_annotation_is_first_meaningful_line() -> void:
    if script_path.is_empty():  return
    for line: String in _lines:
        var stripped := line.strip_edges()
        if stripped.is_empty() or stripped.begins_with("#"):
            continue
        assert_eq(stripped, "@tool", "First meaningful line must be `@tool`")
        return
    fail_test("File appears empty")

func test_has_class_name_in_pascal_case() -> void:
    if script_path.is_empty():  return
    var found := false
    for line: String in _lines:
        var m := RegEx.create_from_string(r"^class_name\s+([A-Z][a-zA-Z0-9_]*)\s*$").search(line)
        if m != null:
            found = true
            break
    assert_true(found, "Missing `class_name` declaration (must be PascalCase)")

func test_no_tween_creation() -> void:
    if script_path.is_empty():  return
    assert_false(_source.contains("create_tween("), "Forbidden: create_tween()")

func test_no_animation_player_reference() -> void:
    if script_path.is_empty():  return
    assert_false(_source.contains("AnimationPlayer"), "Forbidden: AnimationPlayer")

func test_no_await_create_timer() -> void:
    if script_path.is_empty():  return
    var re := RegEx.create_from_string(r"await\s+get_tree\(\)\.create_timer")
    assert_true(re.search(_source) == null, "Forbidden: await get_tree().create_timer()")

func test_no_tween_method_calls() -> void:
    if script_path.is_empty():  return
    var re := RegEx.create_from_string(r"\.tween_")
    assert_true(re.search(_source) == null, "Forbidden: .tween_* method calls")

func test_all_exports_have_setters() -> void:
    if script_path.is_empty():  return
    var export_re := RegEx.create_from_string(r"^@export\s+(?:var\s+)?(\w+)\s*[:=]")
    var missing: Array[String] = []
    for i: int in range(_lines.size()):
        var m := export_re.search(_lines[i])
        if m == null:  continue
        var var_name: String = m.get_string(1)
        var has_setter := false
        for j: int in range(i + 1, mini(i + 5, _lines.size())):
            if _lines[j].strip_edges().begins_with("set("):
                has_setter = true
                break
            elif _lines[j].strip_edges().begins_with("@export") or _lines[j].strip_edges().begins_with("func ") or _lines[j].strip_edges().begins_with("class "):
                break
        if not has_setter:
            missing.append(var_name)
    if not missing.is_empty():
        fail_test("@export vars missing setters: %s" % ", ".join(missing))

func test_all_exports_have_docstring_comments() -> void:
    if script_path.is_empty():  return
    var export_re := RegEx.create_from_string(r"^@export\s+(?:var\s+)?(\w+)\s*[:=]")
    var missing: Array[String] = []
    for i: int in range(_lines.size()):
        var m := export_re.search(_lines[i])
        if m == null:  continue
        var var_name: String = m.get_string(1)
        var has_doc := false
        for j: int in range(i - 1, -1, -1):
            var prev: String = _lines[j].strip_edges()
            if prev.is_empty():  continue
            if prev.begins_with("##"):
                has_doc = true
            break
        if not has_doc:
            missing.append(var_name)
    if not missing.is_empty():
        fail_test("@export vars missing docstring (##): %s" % ", ".join(missing))

func test_has_signals_when_exports_exist() -> void:
    if script_path.is_empty():  return
    var has_export := _source.contains("@export ")
    var has_signal := RegEx.create_from_string(r"^signal\s+\w+").search(_source) != null
    if has_export:
        assert_true(has_signal, "Scene has @export vars but no signals.")
```

### Per-Scene Subclass

For each frontend scene, create a one-line subclass:

```gdscript
class_name TestMyWidgetContract
extends TestFrontendContract

func before_each() -> void:
    script_path = "res://frontend/hud/my_widget.gd"
    super.before_each()
```

### Running Contract Tests

Run all contract tests in a directory:
```bash
godot --headless --script res://addons/gut/gut_cmdln.gd -gdir=res://tests/frontend -gexit
```

Run a single contract test:
```bash
godot --headless --script res://addons/gut/gut_cmdln.gd -gdir=res://tests/frontend -gexit -gselect=test_my_widget_contract
```

### When to Use What

| Validator | Best For |
|-----------|----------|
| `validate_frontend.py` | CI pipelines, pre-commit hooks, quick CLI checks without booting Godot |
| `TestFrontendContract` | Living documentation inside the test suite; catches regressions at test time; integrates with existing GUT workflow |
