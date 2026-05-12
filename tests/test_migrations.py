"""
Migration history integrity tests.

These tests use the Alembic ScriptDirectory API to validate the entire migration
chain offline (no live DB required), catching problems like:
  - Branching histories / multiple heads
  - Missing down-revisions
  - Duplicate revision IDs

They are intentionally dependency-free beyond alembic so they always run fast
inside the pre-commit pytest hook.
"""

import os

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory


@pytest.fixture(scope="module")
def alembic_cfg() -> Config:
    """Return an Alembic Config pointing at the project's alembic.ini."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(project_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    return cfg


@pytest.fixture(scope="module")
def script_dir(alembic_cfg: Config) -> ScriptDirectory:
    return ScriptDirectory.from_config(alembic_cfg)


def test_single_head_revision(script_dir: ScriptDirectory) -> None:
    """There must be exactly one head revision (no un-merged branches)."""
    heads = script_dir.get_heads()
    assert len(heads) == 1, (
        f"Expected a single migration head, found {len(heads)}: {heads}. "
        "Merge the branches with `alembic merge -m 'merge heads'`."
    )


def test_no_duplicate_revision_ids(script_dir: ScriptDirectory) -> None:
    """Every revision must have a unique ID."""
    seen: set[str] = set()
    for rev in script_dir.walk_revisions():
        assert rev.revision not in seen, (
            f"Duplicate revision ID detected: {rev.revision}"
        )
        seen.add(rev.revision)


def test_complete_revision_chain(script_dir: ScriptDirectory) -> None:
    """Every non-base revision must reference a down_revision that exists."""
    all_revisions = {rev.revision for rev in script_dir.walk_revisions()}
    for rev in script_dir.walk_revisions():
        if rev.down_revision is None:
            continue  # Base revision — no parent required.
        down_revs = (
            [rev.down_revision]
            if isinstance(rev.down_revision, str)
            else list(rev.down_revision)
        )
        for down_rev in down_revs:
            assert down_rev in all_revisions, (
                f"Revision {rev.revision} references missing down_revision {down_rev!r}."
            )
