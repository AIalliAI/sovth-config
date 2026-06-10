"""Smoke tests for the sovth-config plugin.

Run with: python -m pytest tests/  (or just: python tests/test_smoke.py)

Tests cover:
- Plugin manifest loads and is valid
- Tool schemas are valid JSON-schema-ish
- Storage layer can roundtrip a list
- Research hook can add/remove items
- Self-eval parser handles typical LLM output
- Klerik review parser handles typical LLM output
- Crossref parser handles typical LLM output
- Character-card metadata extraction works
- Profile invoker validates + builds correct specs
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Make the project root importable
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

# Smoke test: import everything to catch syntax errors
def test_imports():
    import sovth_config  # noqa
    from sovth_config import schemas, tools  # noqa
    from sovth_config.research import (  # noqa
        trigger_research_hook,
        build_global_wiki,
        list_items_with_status,
        cancel_research,
        ReadingListError,
        extract,
        crossref,
        wiki_writer,
        klerik_review,
        podcast,
        self_eval,
        runner,
        character_card,
        profile_invoker,
        storage,
    )
    assert hasattr(sovth_config, "register")


def test_plugin_manifest():
    import yaml
    manifest_path = ROOT / "sovth_config" / "plugin.yaml"
    assert manifest_path.is_file(), f"plugin.yaml not found at {manifest_path}"
    data = yaml.safe_load(manifest_path.read_text())
    assert data["name"] == "sovth-config"
    assert "reading_list" in data["provides_tools"]
    assert "character_card" in data["provides_tools"]
    assert "invoke_profile" in data["provides_tools"]


def test_schemas():
    from sovth_config.schemas import (
        READING_LIST_SCHEMA,
        CHARACTER_CARD_SCHEMA,
        INVOKE_PROFILE_SCHEMA,
    )
    for schema in (READING_LIST_SCHEMA, CHARACTER_CARD_SCHEMA, INVOKE_PROFILE_SCHEMA):
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        params = schema["parameters"]
        assert params["type"] == "object"
        assert "properties" in params


def test_storage_roundtrip():
    from sovth_config.research.storage import (
        load_list, save_list, slugify,
    )

    with tempfile.TemporaryDirectory() as tmp:
        list_dir = Path(tmp) / "test"
        list_dir.mkdir()
        data = load_list(list_dir)
        assert data["schema_version"] == 1
        assert data["items"] == []

        data["items"].append({
            "id": "test-1",
            "source": "https://example.com",
            "type": "url",
            "status": "pending-research",
        })
        save_list(list_dir, data)

        data2 = load_list(list_dir)
        assert len(data2["items"]) == 1, f"expected 1 item, got {len(data2['items'])}: {data2}"
        assert data2["items"][0]["id"] == "test-1"

    assert slugify("Hello World!") == "hello-world"
    assert slugify("https://arxiv.org/abs/1234.5678") == "arxiv-org-abs-1234-5678"


def test_research_hook_add_remove():
    from sovth_config.research import (
        trigger_research_hook, cancel_research, list_items_with_status,
    )
    from sovth_config.research.errors import ReadingListError

    with tempfile.TemporaryDirectory() as tmp:
        list_dir = Path(tmp) / "test"
        list_dir.mkdir()

        # Add a file target
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# test content")
            target = f.name
        try:
            item = trigger_research_hook(list_dir, target, depth="low")
            assert item["status"] == "pending-research"
            assert item["type"] == "file"
            items = list_items_with_status(list_dir)
            assert len(items) == 1

            # Add again should be idempotent
            item2 = trigger_research_hook(list_dir, target, depth="low")
            assert item2["id"] == item["id"]
            assert len(list_items_with_status(list_dir)) == 1

            # Remove
            assert cancel_research(list_dir, target) is True
            items = list_items_with_status(list_dir)
            assert len(items) == 0
        finally:
            os.unlink(target)

        # Bad target
        try:
            trigger_research_hook(list_dir, "/nonexistent/file.md")
        except ReadingListError:
            pass
        else:
            assert False, "expected ReadingListError"


def test_self_eval_parser():
    from sovth_config.research.self_eval import parse_self_eval, should_continue

    passing = '{"accuracy": 9.0, "completeness": 8.5, "sourcing": 8.0, "clarity": 9.0, "notes": "good"}'
    s = parse_self_eval(passing)
    assert s.accuracy == 9.0
    assert should_continue(s) is False

    failing = '{"accuracy": 7.0, "completeness": 9.0, "sourcing": 9.0, "clarity": 9.0}'
    s = parse_self_eval(failing)
    assert should_continue(s) is True
    assert "accuracy=7.0" in s.gaps()


def test_klerik_parser():
    from sovth_config.research.klerik_review import parse_klerik_review

    sample = """\
## Score
8.5

## Strengths
- Excellent organization
- Strong source diversity

## Issues
1. The summary buries the lede in paragraph 2.
2. The Deep Dive section repeats content from Key Concepts.
3. The Sources section is missing a primary source.

## Verdict
polish
"""
    r = parse_klerik_review(sample)
    assert r.score == 8.5
    assert r.verdict == "polish"
    assert len(r.strengths) == 2
    assert len(r.issues) == 3


def test_crossref_parser():
    from sovth_config.research.crossref import parse_crossrefs

    sample = """[
        {"claim": "X happened in 2020", "source_url": "https://example.com/a", "source_title": "A", "excerpt": "X", "confidence": 0.9},
        {"claim": "Y is true", "source_url": "https://example.com/b", "source_title": "B", "excerpt": "Y", "confidence": 0.8}
    ]"""
    refs = parse_crossrefs(sample)
    assert len(refs) == 2
    assert refs[0].confidence == 0.9


def test_character_card_metadata():
    """Extract metadata from a real profile (klerik is always present)."""
    from sovth_config.research.character_card import extract_metadata

    profiles_root = Path(os.path.expanduser("~/.hermes/profiles"))
    klerik = profiles_root / "klerik"
    if not klerik.is_dir():
        return  # skip if klerik not installed

    meta = extract_metadata("klerik")
    assert meta.name == "klerik"
    assert meta.role  # has a role
    assert meta.class_name  # has a class
    # Klerik has a Darwin-28B-REASON model
    assert "Darwin" in meta.model or "model" in meta.role.lower() or meta.model


def test_profile_invoker_validation():
    from sovth_config.research.profile_invoker import invoke_profile
    from sovth_config.research.errors import ReadingListError

    # Good: real profile
    result = invoke_profile("klerik", "review this wiki", mode="ephemeral")
    assert "spec" in result
    assert "instructions" in result
    assert result["spec"]["name"] == "klerik"
    assert result["spec"]["mode"] == "ephemeral"

    # Bad: missing profile
    try:
        invoke_profile("nonexistent-profile-xyz", "test")
    except ReadingListError:
        pass
    else:
        assert False, "expected ReadingListError"


def test_global_wiki_empty():
    from sovth_config.research import build_global_wiki

    with tempfile.TemporaryDirectory() as tmp:
        list_dir = Path(tmp) / "test"
        list_dir.mkdir()
        (list_dir / "wiki").mkdir()
        wiki = build_global_wiki(list_dir, list_name="test")
        assert "No wiki-complete items" in wiki


def test_check_available():
    from sovth_config.tools import check_available
    assert check_available() is True


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def test_runner_session_low():
    from sovth_config.research import trigger_research_hook
    from sovth_config.research.runner import ResearchSession

    with tempfile.TemporaryDirectory() as tmp:
        list_dir = Path(tmp) / "test"
        list_dir.mkdir()
        # Register the item via the hook first so it's in list.yaml
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("test")
            target = f.name
        try:
            item = trigger_research_hook(list_dir, target, depth="low")
            sess = ResearchSession(list_dir=list_dir, item=item, depth="low", max_passes=1)
            step = sess.next_step()
            assert step["step"] == "draft_wiki", f"expected draft_wiki, got {step}"
            assert step["pass"] == 1
        finally:
            os.unlink(target)


def test_data_root_env_override():
    """SOVTH_READING_LIST_ROOT should redirect the data directory."""
    from sovth_config import tools

    with tempfile.TemporaryDirectory() as tmp:
        custom_root = Path(tmp) / "custom-reading-list"
        os.environ["SOVTH_READING_LIST_ROOT"] = str(custom_root)
        try:
            # Re-import to pick up the env var. The constant is evaluated
            # at import, so we have to reload the module.
            import importlib
            importlib.reload(tools)
            assert tools.DATA_ROOT == custom_root
        finally:
            del os.environ["SOVTH_READING_LIST_ROOT"]
            importlib.reload(tools)  # restore default


def test_runner_high_loop_terminates():
    """The high-mode loop should stop when self-eval is passing."""
    from sovth_config.research import trigger_research_hook
    from sovth_config.research.runner import ResearchSession

    with tempfile.TemporaryDirectory() as tmp:
        list_dir = Path(tmp) / "test"
        list_dir.mkdir()
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("test content")
            target = f.name
        try:
            item = trigger_research_hook(list_dir, target, depth="high", max_passes=3)
            sess = ResearchSession(list_dir=list_dir, item=item, depth="high", max_passes=3)
            # Pass 1: draft
            step1 = sess.next_step()
            assert step1["step"] == "draft_wiki"
            # Simulate a passing self-eval
            sess.record_draft(
                content="...",
                self_eval_text='{"accuracy": 9.0, "completeness": 9.0, "sourcing": 9.0, "clarity": 9.0}',
            )
            # Next step should be stop (no Klerik in high mode)
            step2 = sess.next_step()
            assert step2["step"] == "stop", f"expected stop, got {step2}"
        finally:
            os.unlink(target)


# ---------------------------------------------------------------------------
# Run as script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_imports,
        test_plugin_manifest,
        test_schemas,
        test_storage_roundtrip,
        test_research_hook_add_remove,
        test_self_eval_parser,
        test_klerik_parser,
        test_crossref_parser,
        test_character_card_metadata,
        test_profile_invoker_validation,
        test_global_wiki_empty,
        test_check_available,
        test_runner_session_low,
        test_data_root_env_override,
        test_runner_high_loop_terminates,
    ]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failures += 1
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
