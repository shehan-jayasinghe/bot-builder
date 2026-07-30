#!/usr/bin/env python3
"""Finish finance demo seed without Bearer token (direct Mongo + services).

Usage:
  poetry run python scripts/seed_finance_agent_local.py --agent-id 6a4b75c633b2e39a8e174bf7
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from app.config import settings
from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.mongo import connect_mongo, disconnect_mongo, get_motor_db
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.job_log_repository import JobLogRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.sub_agent_repository import SubAgentRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.schemas.sub_agent import CreateSubAgentRequest
from app.schemas.workflow import CreateWorkflowRequest, WorkflowEdge, WorkflowNode
from app.services.knowledgebase_ingest_service import build_knowledgebase_ingest_service
from app.services.sub_agent_service import SubAgentService
from app.services.workflow_service import WorkflowService
from app.schemas.knowledgebase import IngestKnowledgebasePayload

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from scripts.seed_finance_agent import (  # noqa: E402
    PAYMENT_WORKFLOW_EDGES,
    PAYMENT_WORKFLOW_NODES,
    _ingest_payload_from_kb,
)

DATA_DIR = SCRIPT_DIR / "seed_data"
VECTOR_KB_NAME = "Finance Policies"
KEYWORD_KB_NAME = "Card Management FAQ"
WORKFLOW_NAME = "Make a Payment"


async def _load_current_user(db: Any, agent: dict[str, Any]) -> CurrentUser:
    org_id = str(agent["organization_id"])
    user_id = str(agent.get("created_by") or "")
    user_doc: dict[str, Any] | None = None
    if user_id:
        try:
            user_doc = await db[settings.users_collection].find_one({"_id": ObjectId(user_id)})
        except InvalidId:
            user_doc = await db[settings.users_collection].find_one({"_id": user_id})

    org_doc: dict[str, Any] | None = None
    try:
        org_doc = await db[settings.organizations_collection].find_one({"_id": ObjectId(org_id)})
    except InvalidId:
        org_doc = await db[settings.organizations_collection].find_one({"_id": org_id})

    if user_doc is None:
        raise RuntimeError(f"User not found for agent created_by={user_id}")

    return CurrentUser(
        user_id=str(user_doc.get("_id")),
        organization_id=org_id,
        clerk_id=str(user_doc.get("clerk_id") or ""),
        email=str(user_doc.get("email") or ""),
        first_name=str(user_doc.get("first_name") or ""),
        last_name=str(user_doc.get("last_name") or ""),
        user_type=str(user_doc.get("user_type") or "root"),
        is_root=bool(user_doc.get("is_root", True)),
        status=str(user_doc.get("status") or "active"),
        organization_name=str((org_doc or {}).get("name") or "Organization"),
        organization_industry=(org_doc or {}).get("industry"),
    )


def _kb_dict(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "name": document.get("name"),
        "organization_id": document.get("organization_id"),
        "source_type": document.get("source_type"),
        "storage_type": document.get("storage_type"),
        "status": document.get("status"),
        "website_url": document.get("website_url"),
        "crawl_depth": document.get("crawl_depth"),
        "s3_key": document.get("s3_key"),
    }


async def _lookup_job_id(db: Any, kb_id: str) -> str:
    document = await db[settings.job_logs_collection].find_one(
        {"knowledgebase_id": kb_id},
        sort=[("created_at", -1)],
    )
    if document is None:
        raise RuntimeError(f"No job log for knowledge base {kb_id}")
    return str(document["_id"])


async def _ingest_kbs(
    *,
    kb_docs: list[dict[str, Any]],
    agent_id: str,
    file_by_storage: dict[str, Path],
) -> None:
    service = build_knowledgebase_ingest_service()
    db = get_motor_db()
    for document in kb_docs:
        kb = _kb_dict(document)
        if kb["status"] == "ready":
            print(f"  skip ingest {kb['id']} — already ready")
            continue
        file_path = file_by_storage.get(str(kb["storage_type"]))
        if file_path is None:
            raise RuntimeError(f"No seed file for storage_type={kb['storage_type']}")
        job_id = await _lookup_job_id(db, kb["id"])
        s3_key = document.get("s3_key") or f"{kb['organization_id']}/{kb['id']}/{file_path.name}"
        payload = _ingest_payload_from_kb(
            {**kb, "job_id": job_id},
            agent_id=agent_id,
            file_name=Path(str(s3_key)).name,
        )
        payload["s3_key"] = s3_key
        print(f"  ingesting {kb['id']} ({kb['storage_type']})...")
        try:
            await service.run(IngestKnowledgebasePayload.model_validate(payload))
            print(f"  done {kb['id']}")
        except Exception as exc:
            print(f"  FAILED {kb['id']}: {exc}", file=sys.stderr)


async def run(*, agent_id: str) -> None:
    finance_file = DATA_DIR / "finance_policies.txt"
    card_file = DATA_DIR / "card_management_faq.txt"
    if not finance_file.exists() or not card_file.exists():
        raise RuntimeError("Missing scripts/seed_data/*.txt")

    await connect_mongo()
    try:
        db = get_motor_db()
        agent_repo = AgentRepository(db)
        kb_repo = KnowledgebaseRepository(db)

        try:
            agent_oid = ObjectId(agent_id)
        except InvalidId as exc:
            raise RuntimeError(f"Invalid agent id: {agent_id}") from exc
        agent = await db[AgentRepository._COLLECTION].find_one({"_id": agent_oid})
        if agent is None:
            raise RuntimeError(f"Agent not found: {agent_id}")

        org_id = str(agent["organization_id"])
        current_user = await _load_current_user(db, agent)
        print(f"Agent {agent_id} org={org_id}")

        kb_docs = await kb_repo.find_all_by_agent(agent_id=agent_id, organization_id=org_id)
        vector_doc = next((d for d in kb_docs if d.get("name") == VECTOR_KB_NAME), None)
        keyword_doc = next((d for d in kb_docs if d.get("name") == KEYWORD_KB_NAME), None)
        if vector_doc is None or keyword_doc is None:
            raise RuntimeError(
                f"Expected KBs '{VECTOR_KB_NAME}' and '{KEYWORD_KB_NAME}' on agent. Found: "
                f"{[d.get('name') for d in kb_docs]}"
            )

        print("Ingesting knowledge bases...")
        await _ingest_kbs(
            kb_docs=[vector_doc, keyword_doc],
            agent_id=agent_id,
            file_by_storage={"vector": finance_file, "keyword": card_file},
        )

        workflow_repo = WorkflowRepository(db)
        workflow_service = WorkflowService(
            workflow_repository=workflow_repo,
            agent_repository=agent_repo,
        )
        existing_workflows = await workflow_repo.find_all_by_organization(
            organization_id=org_id,
            agent_id=agent_id,
        )
        workflow_doc = next((w for w in existing_workflows if w.get("name") == WORKFLOW_NAME), None)
        if workflow_doc is None:
            print("Creating payment workflow...")
            workflow = await workflow_service.create(
                current_user=current_user,
                request=CreateWorkflowRequest(
                    name=WORKFLOW_NAME,
                    description="Guided payment amount collection workflow",
                    agent_id=agent_id,
                    routing_hint=(
                        "Start when the user wants to pay, make a payment, or set up a payment plan"
                    ),
                    nodes=[WorkflowNode.model_validate(n) for n in PAYMENT_WORKFLOW_NODES],
                    edges=[WorkflowEdge.model_validate(e) for e in PAYMENT_WORKFLOW_EDGES],
                ),
            )
            workflow_id = workflow.id
        else:
            workflow_id = str(workflow_doc["_id"])
            print(f"Workflow already exists: {workflow_id}")

        wf = await workflow_repo.find_by_id_for_organization(
            workflow_id=workflow_id,
            organization_id=org_id,
        )
        if wf and wf.get("status") != "published":
            print("Publishing workflow...")
            await workflow_service.publish(current_user=current_user, workflow_id=workflow_id)
        else:
            print(f"Workflow {workflow_id} status={wf.get('status') if wf else 'missing'}")

        sub_agent_service = SubAgentService(
            sub_agent_repository=SubAgentRepository(db),
            agent_repository=agent_repo,
            tool_repository=ToolRepository(db),
            knowledgebase_repository=kb_repo,
            workflow_repository=workflow_repo,
        )
        vector_id = str(vector_doc["_id"])
        keyword_id = str(keyword_doc["_id"])

        sub_specs = [
            (
                "finance_management",
                "Handles balances, EMIs, payment plans, and savings questions",
                (
                    "You are the finance specialist for ABC Bank. Answer questions about "
                    "loan EMIs, late fees, payment plans, savings interest, overdraft, and "
                    "refunds. Use search_knowledge on Finance Policies before answering. "
                    "Never ask for full card numbers or passwords."
                ),
                [vector_id],
                "Delegate for loan, EMI, savings, balance, refund, or payment plan questions",
            ),
            (
                "card_management",
                "Handles debit/credit card activation, blocking, limits, and disputes",
                (
                    "You are the card management specialist for ABC Bank. Help with card "
                    "activation, lost/stolen blocking, credit limits, PIN reset, international "
                    "travel notices, and charge disputes. Use search_knowledge on Card "
                    "Management FAQ before answering."
                ),
                [keyword_id],
                "Delegate for card activation, block, PIN, limit, or dispute questions",
            ),
        ]

        sub_agent_repo = SubAgentRepository(db)
        for name, description, instructions, kb_ids, routing_hint in sub_specs:
            existing = await sub_agent_repo.find_by_name_for_agent(
                name=name,
                agent_id=agent_id,
                organization_id=org_id,
            )
            if existing is not None:
                print(f"Sub-agent already exists: {name} ({existing['_id']})")
                continue
            print(f"Creating sub-agent {name}...")
            created = await sub_agent_service.create(
                current_user=current_user,
                agent_id=agent_id,
                request=CreateSubAgentRequest(
                    name=name,
                    description=description,
                    instructions=instructions,
                    knowledge_base_ids=kb_ids,
                    routing_hint=routing_hint,
                ),
            )
            print(f"  {name} id={created.id}")

        print("\n--- Local seed complete ---")
        print(f"Agent ID:    {agent_id}")
        print(f"Vector KB:   {vector_id}")
        print(f"Keyword KB:  {keyword_id}")
        print(f"Workflow ID: {workflow_id}")
        api_base = os.environ.get("API_BASE", "http://localhost:8000/api/v1")
        print(f"Preview:     POST {api_base}/agents/{agent_id}/preview/chat")
    finally:
        await disconnect_mongo()


def main() -> None:
    parser = argparse.ArgumentParser(description="Finish finance demo seed locally (no JWT)")
    parser.add_argument("--agent-id", required=True)
    args = parser.parse_args()
    asyncio.run(run(agent_id=args.agent_id))


if __name__ == "__main__":
    main()
