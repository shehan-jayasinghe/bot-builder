from app.infrastructure.connectors.neo4j.neo4j_connector import normalize_rel_type


def test_normalize_rel_type_converts_spaces() -> None:
    assert normalize_rel_type("part of") == "PART_OF"


def test_normalize_rel_type_preserves_snake_case() -> None:
    assert normalize_rel_type("RELATED_TO") == "RELATED_TO"


def test_normalize_rel_type_defaults_when_empty() -> None:
    assert normalize_rel_type("   ") == "RELATED_TO"


def test_normalize_rel_type_prefixes_leading_digit() -> None:
    assert normalize_rel_type("123") == "REL_123"
