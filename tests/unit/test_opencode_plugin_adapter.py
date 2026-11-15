# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline checks for the native OpenCode-only EGM plugin."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT
HARNESS = Path(__file__).resolve().parent / "opencode_plugin_harness.mjs"
REVIEWER_IDS = (
    "egm-codebase-details",
    "egm-comprehension",
    "egm-design",
    "egm-implementation-readiness",
    "egm-inventive-catalyst",
    "egm-structural",
    "egm-style",
    "egm-zoom-out",
)
SKILL_IDS = (
    "egm-bootstrap",
    "egm-brainstorm",
    "egm-draft",
    "egm-drift-report",
    "egm-resolve",
    "egm-review",
    "egm-review-loop",
)
PERSONAS = {
    "egm-codebase-details": "codebase_details",
    "egm-comprehension": "comprehension",
    "egm-design": "design_critic",
    "egm-implementation-readiness": "implementation_readiness",
    "egm-inventive-catalyst": "inventive_catalyst",
    "egm-structural": "structural",
    "egm-style": "style",
    "egm-zoom-out": "zoom_out",
}
TEXT_SUFFIXES = {".js", ".json", ".md", ".txt", ".yaml", ".yml"}


def _load() -> tuple[dict, dict]:
    """Load the adapter modules with their sibling import intact."""
    sys.path.insert(0, str(ADAPTER))
    try:
        build_spec = importlib.util.spec_from_file_location("build", ADAPTER / "build.py")
        build = importlib.util.module_from_spec(build_spec)
        sys.modules["build"] = build
        build_spec.loader.exec_module(build)
        install_spec = importlib.util.spec_from_file_location(
            "egm_opencode_install", ADAPTER / "install.py"
        )
        install = importlib.util.module_from_spec(install_spec)
        install_spec.loader.exec_module(install)
    finally:
        sys.path.remove(str(ADAPTER))
        sys.modules.pop("build", None)
    return vars(build), vars(install)


BUILD, INSTALL = _load()


def _files(directory: Path) -> set[str]:
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_build_ships_only_opencode_pieces(tmp_path: Path) -> None:
    destination = BUILD["build"](tmp_path / "egm")
    files = _files(destination)

    assert {
        "index.js",
        "package.json",
        "manifest.json",
        "bundle/docs/opencode-plugin.md",
        "bundle/resources/README.md",
        "bundle/resources/execution_instructions.md",
    } <= files
    assert not [name for name in files if "openai.yaml" in name]
    assert not [name for name in files if name.endswith(("TEST.md", "test_scenarios.yaml"))]
    assert not [name for name in files if "/assets/" in f"/{name}"]

    assert {name.removeprefix("bundle/agents/").removesuffix(".md")
            for name in files if name.startswith("bundle/agents/")} == {
        "codebase_details",
        "comprehension",
        "design_critic",
        "implementation_readiness",
        "inventive_catalyst",
        "structural",
        "style",
        "zoom_out",
    }
    assert {name.split("/")[2] for name in files if name.startswith("bundle/skills/")} == set(
        SKILL_IDS
    )
    for skill in SKILL_IDS:
        assert f"bundle/skills/{skill}/SKILL.md" in files
    assert "bundle/skills/egm-bootstrap/references/templates.md" in files
    assert "bundle/skills/egm-bootstrap/references/worker-return.schema.json" not in files
    assert "bundle/skills/egm-draft/references/design_doc.md" in files

    manifest = json.loads((destination / "manifest.json").read_text())
    canonical = json.loads((ROOT / "src" / "plugin.json").read_text())
    assert manifest["name"] == canonical["name"]
    assert manifest["version"] == canonical["version"]
    assert manifest["interface"] == "opencode-plugin"
    assert manifest["tested_host"] == "2.2.7"
    assert manifest["targets"] == ["opencode"]
    assert set(manifest["sha256"]) == files - {"manifest.json"}
    for relative, digest in manifest["sha256"].items():
        assert hashlib.sha256((destination / relative).read_bytes()).hexdigest() == digest

    package = json.loads((destination / "package.json").read_text())
    assert package["name"] == "opencode-egm"
    assert package["exports"] == {".": "./index.js"}

    # The runtime guide is generated from the adapter source, not the canonical docs.
    assert (destination / "bundle/docs/opencode-plugin.md").read_bytes() == (
        ADAPTER / "src/opencode-plugin.md"
    ).read_bytes()


def test_build_contains_no_other_agent_instructions(tmp_path: Path) -> None:
    destination = BUILD["build"](tmp_path / "egm")
    forbidden = BUILD["FORBIDDEN"]
    for path in sorted(destination.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        match = forbidden.search(path.read_text(encoding="utf-8"))
        assert match is None, f"{path.relative_to(destination)}: {match.group(0)!r}"


def test_skills_are_rewritten_for_opencode(tmp_path: Path) -> None:
    bundle = BUILD["build"](tmp_path / "egm") / "bundle/skills"
    review = (bundle / "egm-review/SKILL.md").read_text()
    assert "`subagent` tool" in review
    assert "runs in the background" in review
    assert "`question` tool" in review
    assert "/egm:egm-" not in review

    draft = (bundle / "egm-draft/SKILL.md").read_text()
    assert "skill picker" not in draft

    bootstrap = (bundle / "egm-bootstrap/SKILL.md").read_text()
    assert "Sequential Execution Strategy" in bootstrap
    assert "Sub-Orchestrator" not in bootstrap
    assert "sub-orchestrator" not in bootstrap
    assert "is_worker" not in bootstrap
    assert "sub_tree_root" not in bootstrap
    assert "goldfish-explorer" not in bootstrap
    assert "run the\n    read-only scout inline" in bootstrap
    assert "`.opencode`" in bootstrap
    assert "Step 4: Directory Contract Flow" in bootstrap

    for skill in SKILL_IDS:
        text = (bundle / skill / "SKILL.md").read_text()
        assert "`ask_question`" not in text
        assert "plain chat" not in text


def test_build_fails_when_new_foreign_text_appears(tmp_path: Path) -> None:
    source = (ROOT / "canonical/skills/egm-review/SKILL.md").read_text()
    with pytest.raises(ValueError, match="non-OpenCode text remains"):
        BUILD["rewrite_skill"](
            source + "\nRead docs/codex.md before reviewing.\n", "egm-review"
        )


def test_build_fails_when_an_upstream_rewrite_stops_matching() -> None:
    with pytest.raises(ValueError, match="Rewrite no longer matches"):
        BUILD["_apply"]("nothing here", re.compile("gone"), "", "missing")


def test_install_refuses_to_replace_an_existing_plugin(tmp_path: Path) -> None:
    config = tmp_path / "config"
    destination = INSTALL["install"](config, tmp_path / "built")
    installed = _files(destination)
    marker = destination / "bundle/docs/opencode-plugin.md"
    before = marker.read_bytes()

    with pytest.raises(FileExistsError):
        INSTALL["install"](config, tmp_path / "built")
    assert _files(destination) == installed
    assert marker.read_bytes() == before
    assert json.loads((destination / "manifest.json").read_text())["targets"] == ["opencode"]


def test_install_tracks_the_expected_plugin_name(tmp_path: Path) -> None:
    destination = INSTALL["install"](tmp_path / "config", tmp_path / "built")
    assert destination == (tmp_path / "config").resolve() / "plugins" / "egm"
    assert (destination / "index.js").is_file()


def test_prior_artifacts_reports_a_discovery_based_install(tmp_path: Path) -> None:
    assert INSTALL["prior_artifacts"](tmp_path) == []
    for relative in ("agents/egm.md", "commands/egm-review.md", "skills/egm-review"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".md"):
            path.write_text("stale")
        else:
            path.mkdir()
    assert INSTALL["prior_artifacts"](tmp_path) == [
        tmp_path / "agents/egm.md",
        tmp_path / "commands/egm-review.md",
        tmp_path / "skills/egm-review",
    ]


def test_uninstall_removes_only_the_plugin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config"
    destination = INSTALL["install"](config, tmp_path / "built")
    keep = config / "opencode.json"
    keep.write_text("{}")

    monkeypatch.setattr(sys, "argv", ["install.py", "--config-dir", str(config), "--uninstall"])
    INSTALL["main"]()
    assert not destination.exists()
    assert keep.read_text() == "{}"


def test_plugin_registers_native_transforms(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed in local environment")
    destination = BUILD["build"](tmp_path / "egm")
    result = subprocess.run(
        [node, str(HARNESS), str(destination)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)

    assert data["id"] == "egm"
    agents = {agent["id"]: agent for agent in data["agents"]}
    assert set(agents) == set(REVIEWER_IDS) | {"egm"}

    for agent_id in REVIEWER_IDS:
        agent = agents[agent_id]
        assert agent["mode"] == "subagent"
        assert agent["description"]
        assert "fresh child session" in agent["system"]
        assert f"bundle/agents/{PERSONAS[agent_id]}.md" in agent["system"]
        assert agent["permissions"][-9:] == [
            {"action": "*", "resource": "*", "effect": "deny"},
            {"action": "read", "resource": "*", "effect": "allow"},
            {"action": "read", "resource": "*.env", "effect": "deny"},
            {"action": "read", "resource": "*.env.*", "effect": "deny"},
            {"action": "read", "resource": "*.env.example", "effect": "allow"},
            {"action": "glob", "resource": "*", "effect": "allow"},
            {"action": "grep", "resource": "*", "effect": "deny"},
            {"action": "external_directory", "resource": "*", "effect": "deny"},
            {
                "action": "external_directory",
                "resource": f"{destination.resolve()}/bundle/*",
                "effect": "allow",
            },
        ]

    orchestrator = agents["egm"]
    assert orchestrator["mode"] == "primary"
    for agent_id in REVIEWER_IDS:
        assert {"action": "subagent", "resource": agent_id, "effect": "allow"} in orchestrator[
            "permissions"
        ]
        assert agent_id in orchestrator["system"]
    assert {"action": "subagent", "resource": "*", "effect": "deny"} in orchestrator[
        "permissions"
    ]
    assert {"action": "skill", "resource": "egm-*", "effect": "allow"} in orchestrator[
        "permissions"
    ]
    assert not any(call[0] == "agent.default" for call in data["calls"])

    assert data["commands"] == list(SKILL_IDS)
    assert {skill["id"] for skill in data["skills"]} == set(SKILL_IDS)
    for skill in data["skills"]:
        assert skill["autoinvoke"] is False
        assert skill["description"]
        assert Path(skill["path"]).is_file()
        assert not skill["content"].startswith("---")

    calls = data["calls"]
    assert [call[0] for call in calls] == ["switchAgent", "prompt"]
    assert calls[0][1] == {"sessionID": "ses_harness", "agent": "egm"}
    assert calls[1][1]["sessionID"] == "ses_harness"
    assert calls[1][1]["delivery"] == "queue"
    assert "Read and execute" in calls[1][1]["text"]
    assert f"{destination.resolve()}/bundle/skills/egm-review/SKILL.md" in calls[1][1]["text"]
    assert "Review /tmp/design.md" in calls[1][1]["text"]
