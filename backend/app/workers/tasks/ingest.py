from app.schemas.knowledgebase import IngestKnowledgebasePayload
from app.services.knowledgebase_ingest_service import build_knowledgebase_ingest_service
from app.workers.celery_app import celery_app
from app.workers.runtime import run_async_task


@celery_app.task(name="ingest_knowledgebase")
def ingest_knowledgebase(payload: dict) -> None:
    """Flow 4 + 5 — extract, chunk, and index a knowledge base."""
    ingest_payload = IngestKnowledgebasePayload.model_validate(payload)

    async def _run() -> None:
        service = build_knowledgebase_ingest_service()
        await service.run(ingest_payload)

    run_async_task(_run())
