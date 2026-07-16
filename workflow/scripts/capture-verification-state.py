#!/usr/bin/env python3
"""Capture or inspect a deterministic verification state fingerprint."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def load_validator():
    path = Path(__file__).with_name("validate-platform-change.py")
    spec = importlib.util.spec_from_file_location("platform_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load platform validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(root: Path, platform: str, feature: str, change: str | None, write: bool) -> tuple[dict[str, object], Path]:
    validator = load_validator()
    repo = root.resolve()
    adapter = validator.load_adapter(repo, platform)
    validator.require_capability(adapter, "verify")
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "verify")
    meta_path = package / "meta.json"
    if not meta_path.is_file():
        raise ValueError(f"missing package meta for {feature}/{change_id}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    state = validator.compute_state(repo, adapter, package, meta)
    state["captured_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target = package / "evidence" / "verification-state.json"
    if write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state, target


def self_test() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve()
        adapter, package, _meta = validator.write_fixture(repo)
        meta = json.loads((package / "meta.json").read_text())
        before = validator.compute_state(repo, adapter, package, meta)
        terminal_inputs = (
            (repo / "workflow/rules/verification-evidence.md", "common evidence policy"),
            (repo / "workflow/phases/verify.md", "common verify phase"),
            (repo / "TestClient/workflow/phases/verify.md", "platform verify addendum"),
        )
        for terminal_input, label in terminal_inputs:
            original = terminal_input.read_text(encoding="utf-8")
            terminal_input.write_text(original + "Terminal contract changed.\n", encoding="utf-8")
            changed = validator.compute_state(repo, adapter, package, meta)
            assert changed["fingerprint"] != before["fingerprint"], f"{label} mutation must stale fingerprint"
            terminal_input.write_text(original, encoding="utf-8")
            restored = validator.compute_state(repo, adapter, package, meta)
            assert restored == before, f"restored {label} must restore fingerprint"

        common_policy = repo / "workflow/rules/verification-evidence.md"
        original_policy = common_policy.read_text(encoding="utf-8")
        common_policy.unlink()
        try:
            validator.compute_state(repo, adapter, package, meta)
            raise AssertionError("missing common evidence policy passed")
        except validator.AdapterError as error:
            assert "required terminal verification input is missing" in str(error)
        finally:
            common_policy.write_text(original_policy, encoding="utf-8")
        assert validator.compute_state(repo, adapter, package, meta) == before

        for platform in ("iOS", "Android"):
            platform_phase = repo / platform / "workflow/phases/verify.md"
            platform_phase.parent.mkdir(parents=True, exist_ok=True)
            original = f"Current {platform} verification addendum.\n"
            platform_phase.write_text(original, encoding="utf-8")
            platform_adapter = json.loads(json.dumps(adapter))
            platform_adapter["platform_name"] = platform
            platform_adapter["platform_root"] = platform
            platform_before = validator.compute_state(repo, platform_adapter, package, meta)
            platform_phase.write_text(original + "Platform contract changed.\n", encoding="utf-8")
            platform_changed = validator.compute_state(repo, platform_adapter, package, meta)
            assert platform_changed["fingerprint"] != platform_before["fingerprint"], (
                f"{platform} verify addendum mutation must stale fingerprint"
            )
            platform_phase.write_text(original, encoding="utf-8")
            assert validator.compute_state(repo, platform_adapter, package, meta) == platform_before

        design = package / "design.md"
        design.write_text(design.read_text() + "\nA current contract detail changed.\n")
        after = validator.compute_state(repo, adapter, package, meta)
        assert before["fingerprint"] != after["fingerprint"], "contract mutation must change fingerprint"
        design.write_text(design.read_text().replace("\nA current contract detail changed.\n", ""))
        restored = validator.compute_state(repo, adapter, package, meta)
        assert restored == before, "restored content must restore fingerprint"
        verification = package / "verification.md"; original_verification = verification.read_text()
        verification.write_text(original_verification.replace("pending", "FAIL", 1))
        changed_verification = validator.compute_state(repo, adapter, package, meta)
        assert changed_verification["fingerprint"] != before["fingerprint"], "verification mutation must stale fingerprint"
        verification.write_text(original_verification)
        evidence = package / "evidence"; evidence.mkdir()
        proof = evidence / "task-001.md"; proof.write_text("Initial proof.\n")
        with_evidence = validator.compute_state(repo, adapter, package, meta)
        assert with_evidence["fingerprint"] != before["fingerprint"], "adding evidence must stale fingerprint"
        proof.write_text("Changed proof.\n")
        changed_evidence = validator.compute_state(repo, adapter, package, meta)
        assert changed_evidence["fingerprint"] != with_evidence["fingerprint"], "evidence content must affect fingerprint"
        proof.unlink()
        state_file = evidence / "verification-state.json"; state_file.write_text("{}\n")
        excluded_state = validator.compute_state(repo, adapter, package, meta)
        assert excluded_state == before, "verification-state.json must not self-reference"
        selected_rule = repo / "TestClient/workflow/application.md"
        selected_rule.write_text("Changed selected rule.\n")
        selected = validator.compute_state(repo, adapter, package, meta)
        assert selected["fingerprint"] != before["fingerprint"], "selected rule must stale fingerprint"
        selected_rule.write_text("Current selected application rule.\n")
        unselected_rule = repo / "TestClient/workflow/performance-a.md"
        unselected_rule.write_text("Changed unselected rule.\n")
        unselected = validator.compute_state(repo, adapter, package, meta)
        assert unselected == before, "unselected rule must not stale fingerprint"
        unselected_rule.write_text("Unselected performance rule A.\n")
        adapter["scope_rule_profiles"]["performance"].reverse()
        unselected_profile = validator.compute_state(repo, adapter, package, meta)
        assert unselected_profile == before, "unselected scope mapping must not stale fingerprint"
    print("capture-verification-state self-test: PASS (deterministic and stale-sensitive)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform")
    parser.add_argument("--feature")
    parser.add_argument("--change")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.platform or not args.feature:
        parser.error("--platform and --feature are required")
    try:
        state, target = capture(args.root, args.platform, args.feature, args.change, args.write)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"BLOCKED: {error}; no state was accepted.")
        return 2
    action = "written" if args.write else "dry-run"
    print(f"Verification state {action}: {target.relative_to(args.root.resolve())}")
    print(state["fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
