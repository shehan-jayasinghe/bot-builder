from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.evaluation import get_rag_evaluation_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.evaluation import (
    EvalRunResponse,
    EvalRunStatus,
    EvalScores,
    EvalThresholds,
)
from app.services.rag_evaluation_service import RagEvaluationService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.evaluation import EvaluationDisabledError, EvalRunNotFoundError

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
RUN_ID = "6a3b7c61d8139334274fbb01"


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="6a3b7c61d8139334274fbbfd",
        organization_id=ORG_ID,
        clerk_id="user_test",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        user_type="root",
        is_root=True,
        status="active",
        organization_name="abc bank",
        organization_industry="financial_services",
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def _sample_run_response() -> EvalRunResponse:
    return EvalRunResponse(
        run_id=RUN_ID,
        status=EvalRunStatus.COMPLETE,
        scores=EvalScores(
            faithfulness=0.75,
            answer_relevancy=0.92,
            context_precision=0.89,
            context_recall=0.80,
        ),
        thresholds=EvalThresholds(faithfulness=0.8, context_precision=0.7),
        passed=False,
    )


def test_run_evaluation_returns_scores(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.run_single.return_value = _sample_run_response()
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/evaluations/run",
        json={
            "question": "What is the minimum balance?",
            "ground_truth": "Urban ₹10,000",
            "mode": "full_bot",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == RUN_ID
    assert body["scores"]["faithfulness"] == 0.75
    assert body["passed"] is False
    mock_service.run_single.assert_awaited_once()


def test_run_evaluation_disabled_returns_503(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.run_single.side_effect = EvaluationDisabledError("disabled")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/evaluations/run",
        json={"question": "Hello"},
    )

    assert response.status_code == 503


def test_get_evaluation_run_not_found(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.get_run.side_effect = EvalRunNotFoundError("missing")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/evaluations/runs/{RUN_ID}")

    assert response.status_code == 404


def test_dummy_dataset_endpoint(client: TestClient) -> None:
    from datetime import UTC, datetime

    from app.schemas.evaluation import EvalDatasetCase, EvalDummyDatasetResponse

    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.get_dummy_dataset.return_value = EvalDummyDatasetResponse(
        name="Financial — Payment Collections (builtin)",
        industry="financial_services",
        agent_type="payment_collections",
        cases=[
            EvalDatasetCase(
                question="What is the minimum balance for urban savings?",
                ground_truth="Urban minimum balance is ₹10,000.",
            ),
        ],
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/evaluations/datasets/dummy")

    assert response.status_code == 200
    body = response.json()
    assert body["industry"] == "financial_services"
    assert len(body["cases"]) == 1


def test_create_dataset_returns_201(client: TestClient) -> None:
    from app.schemas.evaluation import EvalDatasetResponse

    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.create_dataset.return_value = EvalDatasetResponse(
        dataset_id="6a3b7c61d8139334274fbb02",
        name="Regression set",
        case_count=1,
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/evaluations/datasets",
        json={
            "name": "Regression set",
            "cases": [{"question": "Hi?", "ground_truth": "Hello"}],
        },
    )

    assert response.status_code == 201
    assert response.json()["case_count"] == 1


def test_run_evaluation_agent_not_found(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RagEvaluationService)
    mock_service.run_single.side_effect = AgentNotFoundError("missing")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_evaluation_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/evaluations/run",
        json={"question": "Hello"},
    )

    assert response.status_code == 404
