from app.domain.evaluation.dataset_loader import load_builtin_dataset


def test_load_builtin_dataset_for_financial_payment_collections() -> None:
    data = load_builtin_dataset(
        industry="financial_services",
        agent_type="payment_collections",
    )
    assert data["industry"] == "financial_services"
    assert data["agent_type"] == "payment_collections"
    assert len(data["cases"]) >= 1
    assert "minimum balance" in data["cases"][0]["question"].lower()


def test_load_builtin_dataset_falls_back_to_generic() -> None:
    data = load_builtin_dataset(industry="travel", agent_type="unknown_type")
    assert data["industry"] == "other"
    assert data["agent_type"] == "generic"
    assert len(data["cases"]) >= 1
