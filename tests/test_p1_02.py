"""P1-02: decomposer per-item validation."""

from src.agents.decomposer import _parse_sub_issues_json


def test_bad_item_does_not_discard_all():
    raw = '[{"id": 1, "title": "A", "description": "x"}, "junk", {"id": 2, "title": "B", "description": "y"}]'
    items = _parse_sub_issues_json(raw)
    assert len(items) == 2
    assert items[0].title == "A"
