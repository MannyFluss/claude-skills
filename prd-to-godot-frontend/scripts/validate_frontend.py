#!/usr/bin/env python3
"""
validate_frontend.py

Validates a Godot GDScript frontend scene against the prd-to-godot-frontend skill rules.

Usage:
    python validate_frontend.py path/to/scene_name.gd

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import argparse
import re
import sys
from pathlib import Path


class Validator:
    def __init__(self, source: str, filepath: Path):
        self.source = source
        self.filepath = filepath
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def check_tool_annotation(self) -> None:
        """@tool must be the first meaningful line."""
        lines = self.source.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "@tool":
                return
            self.fail("Missing `@tool` annotation (must be first meaningful line).")
            return
        self.fail("Missing `@tool` annotation (file appears empty).")

    def check_class_name(self) -> None:
        """Must declare class_name in PascalCase."""
        pattern = re.compile(r"^class_name\s+([A-Z][a-zA-Z0-9_]*)\s*$", re.MULTILINE)
        if not pattern.search(self.source):
            self.fail("Missing `class_name` declaration (must be PascalCase).")

    def check_no_forbidden_patterns(self) -> None:
        """No Tween, AnimationPlayer, or create_timer usage."""
        forbidden = [
            (r"create_tween\s*\(", "Tween creation (create_tween)"),
            (r"AnimationPlayer", "AnimationPlayer reference"),
            (r"await\s+get_tree\(\)\.create_timer", "await create_timer"),
            (r"\.tween_", "Tween method call (.tween_*)"),
        ]
        for pat, desc in forbidden:
            if re.search(pat, self.source):
                self.fail(f"Forbidden pattern found: {desc}.")

    def check_export_setters(self) -> None:
        """Every @export must have a setter block with validation logic."""
        # Find all @export declarations
        export_pattern = re.compile(
            r"^@export\s+(?:var\s+)?(\w+)\s*:", re.MULTILINE
        )
        exports = export_pattern.findall(self.source)

        for var_name in exports:
            # Look for a setter block immediately following this export
            # This is a heuristic: search for 'set(value):' or 'set(v):' after the export line
            escaped = re.escape(var_name)
            setter_pattern = re.compile(
                rf"@export\s+(?:var\s+)?{escaped}\s*[=:]\s*[^\n]*\n\s+set\s*\(",
                re.MULTILINE,
            )
            if not setter_pattern.search(self.source):
                self.fail(
                    f"`@export var {var_name}` missing a setter block with validation."
                )

    def check_export_docstrings(self) -> None:
        """Every @export should be preceded by a docstring comment (##)."""
        lines = self.source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("@export"):
                # Check preceding non-empty lines for docstring
                has_doc = False
                for j in range(i - 1, -1, -1):
                    prev = lines[j].strip()
                    if not prev:
                        continue
                    if prev.startswith("##"):
                        has_doc = True
                    break
                if not has_doc:
                    # Extract var name for the message
                    m = re.search(r"@export\s+(?:var\s+)?(\w+)", stripped)
                    name = m.group(1) if m else "?"
                    self.warn(
                        f"`@export var {name}` missing docstring comment (##) above it."
                    )

    def check_signals(self) -> None:
        """Should declare at least one signal if there are @export vars that change state."""
        has_export = bool(re.search(r"^@export\s", self.source, re.MULTILINE))
        has_signal = bool(re.search(r"^signal\s+\w+", self.source, re.MULTILINE))
        if has_export and not has_signal:
            self.warn(
                "Scene has @export vars but no signals. Consider emitting signals on state changes."
            )

    def check_no_hardcoded_position(self) -> None:
        """Warn on direct position/scale/modulate/size assignment outside setters."""
        # Heuristic: look for direct assignment patterns in function bodies
        bad = re.compile(
            r"^\s+(position|scale|modulate|size)\s*[=+\-*/]\s*[^\n]+", re.MULTILINE
        )
        matches = bad.findall(self.source)
        if matches:
            self.warn(
                f"Possible hardcoded transform assignment: {set(matches)}. "
                "Ensure these are inside setter-driven reactive updates only."
            )

    def run(self) -> bool:
        self.check_tool_annotation()
        self.check_class_name()
        self.check_no_forbidden_patterns()
        self.check_export_setters()
        self.check_export_docstrings()
        self.check_signals()
        self.check_no_hardcoded_position()

        print(f"Validating: {self.filepath}")
        print("-" * 40)
        if self.warnings:
            for w in self.warnings:
                print(f"  WARNING: {w}")
        if self.errors:
            for e in self.errors:
                print(f"  ERROR: {e}")
        if not self.warnings and not self.errors:
            print("  All checks passed.")
            return True

        print("-" * 40)
        print(f"Result: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        return len(self.errors) == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Godot frontend GDScript against prd-to-godot-frontend rules."
    )
    parser.add_argument("filepath", type=Path, help="Path to the .gd file")
    args = parser.parse_args()

    if not args.filepath.exists():
        print(f"File not found: {args.filepath}")
        return 1

    source = args.filepath.read_text(encoding="utf-8")
    validator = Validator(source, args.filepath)
    ok = validator.run()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
