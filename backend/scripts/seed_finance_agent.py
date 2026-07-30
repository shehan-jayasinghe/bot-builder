#!/usr/bin/env python3
"""Seed a finance/card management agentic demo via REST API.

Usage:
  export BEARER_TOKEN='eyJ...'
  export CLERK_SESSION_ID='sess_...'   # auto-mint via Backend API
  poetry run python scripts/seed_finance_agent.py

Optional:
  API_BASE=http://localhost:8000/api/v1 poetry run python scripts/seed_finance_agent.py
  poetry run python scripts/seed_finance_agent.py --sync-ingest
  poetry run python scripts/seed_finance_agent.py --agent-id <id> --sync-ingest
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "seed_data"

PAYMENT_WORKFLOW_NODES = [
    {"id": "start-1", "type": "start", "position": {"x": 80, "y": 200}, "data": {}},
    {
        "id": "msg-1",
        "type": "message",
        "position": {"x": 280, "y": 200},
        "data": {
            "text": "I'll help you make a payment today.",
            "buttons": [{"title": "Continue", "payload": "continue"}],
        },
    },
    {
        "id": "input-1",
        "type": "input",
        "position": {"x": 480, "y": 200},
        "data": {
            "slot_name": "payment_amount",
            "prompt": "Enter the payment amount in USD (e.g. 150.00):",
            "validation": "number",
            "retry_message": "Please enter a valid number for the payment amount.",
        },
    },
    {
        "id": "out-1",
        "type": "output",
        "position": {"x": 680, "y": 200},
        "data": {"text": "Thank you. We will process your payment of ${{payment_amount}}."},
    },
    {
        "id": "end-1",
        "type": "end",
        "position": {"x": 880, "y": 200},
        "data": {"text": "Payment request recorded. Return to the assistant anytime."},
    },
]

PAYMENT_WORKFLOW_EDGES = [
    {"id": "edge-1", "source": "start-1", "target": "msg-1"},
    {"id": "edge-2", "source": "msg-1", "target": "input-1"},
    {"id": "edge-3", "source": "input-1", "target": "out-1"},
    {"id": "edge-4", "source": "out-1", "target": "end-1"},
]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _api_base() -> str:
    return os.environ.get("API_BASE", "http://localhost:8000/api/v1").rstrip("/")


def _require_token() -> str:
    token = os.environ.get("BEARER_TOKEN", "").strip()
    if token:
        return token
    session_id = os.environ.get("CLERK_SESSION_ID", "").strip()
    if session_id:
        from scripts.clerk_mint_token import mint_session_token

        print(f"Minting JWT from Clerk session {session_id}...")
        return mint_session_token(session_id=session_id)
    print(
        "Set BEARER_TOKEN or CLERK_SESSION_ID (mint via scripts/clerk_mint_token.py).",
        file=sys.stderr,
    )
    sys.exit(1)


def _check_response(response: httpx.Response, step: str) -> dict:
    if response.is_success:
        return response.json() if response.content else {}
    print(f"[{step}] {response.status_code} {response.text}", file=sys.stderr)
    sys.exit(1)


async def _run_sync_ingests(
    *,
    kb_files: list[tuple[dict, Path]],
    agent_id: str,
) -> None:
    from app.config import settings
    from app.infrastructure.db.mongo import connect_mongo, disconnect_mongo, get_motor_db
    from app.schemas.knowledgebase import IngestKnowledgebasePayload
    from app.services.knowledgebase_ingest_service import build_knowledgebase_ingest_service

    await connect_mongo()
    try:
        db = get_motor_db()
        payloads: list[dict] = []
        for kb, file_path in kb_files:
            if kb.get("status") == "ready":
                print(f"  skip {kb['id']} — already ready")
                continue
            job_id = kb.get("job_id")
            if not job_id:
                document = await db[settings.job_logs_collection].find_one(
                    {"knowledgebase_id": kb["id"]},
                    sort=[("created_at", -1)],
                )
                if document is None:
                    raise RuntimeError(f"No job log found for knowledge base {kb['id']}")
                job_id = str(document["_id"])
            payloads.append(
                _ingest_payload_from_kb(
                    {**kb, "job_id": job_id},
                    agent_id=agent_id,
                    file_name=file_path.name,
                )
            )

        if not payloads:
            return

        service = build_knowledgebase_ingest_service()
        for payload in payloads:
            await service.run(IngestKnowledgebasePayload.model_validate(payload))
            print(f"  ingested {payload['knowledgebase_id']} ({payload['storage_type']})")
    finally:
        await disconnect_mongo()


def _load_agent_kbs(client: httpx.Client, *, token: str, agent_id: str) -> list[dict]:
    response = client.get(
        f"{_api_base()}/agents/{agent_id}/knowledgebases",
        headers=_headers(token),
    )
    data = _check_response(response, "list_agent_kbs")
    return data.get("items") or []


def _pick_kb(items: list[dict], *, storage_type: str, name: str) -> dict:
    for item in items:
        if item.get("storage_type") == storage_type and item.get("name") == name:
            return item
    print(f"KB not found: {name} ({storage_type})", file=sys.stderr)
    sys.exit(1)


def _ingest_payload_from_kb(kb: dict, *, agent_id: str, file_name: str) -> dict:
    org_id = kb["organization_id"]
    kb_id = kb["id"]
    return {
        "knowledgebase_id": kb_id,
        "job_id": kb["job_id"],
        "organization_id": org_id,
        "source_type": kb["source_type"],
        "storage_type": kb["storage_type"],
        "website_url": kb.get("website_url"),
        "crawl_depth": kb.get("crawl_depth"),
        "agent_id": agent_id,
        "s3_key": f"{org_id}/{kb_id}/{file_name}",
    }


def create_knowledgebase(
    client: httpx.Client,
    *,
    token: str,
    agent_id: str,
    name: str,
    storage_type: str,
    file_path: Path,
    routing_hint: str,
) -> dict:
    with file_path.open("rb") as handle:
        response = client.post(
            f"{_api_base()}/knowledgebases",
            headers=_headers(token),
            data={
                "name": name,
                "description": f"Demo {storage_type} KB for {name}",
                "source_type": "file",
                "storage_type": storage_type,
                "agent_id": agent_id,
                "routing_hint": routing_hint,
            },
            files={"file": (file_path.name, handle, "text/plain")},
            timeout=120.0,
        )
    return _check_response(response, f"create_kb:{name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed finance/card agentic demo")
    parser.add_argument(
        "--sync-ingest",
        action="store_true",
        help="Run ingest in-process after KB create (no Celery worker required)",
    )
    parser.add_argument(
        "--agent-id",
        help="Resume an existing agent (skip agent/KB create; finish ingest + workflow + sub-agents)",
    )
    args = parser.parse_args()
    token = _require_token()

    finance_file = DATA_DIR / "finance_policies.txt"
    card_file = DATA_DIR / "card_management_faq.txt"
    if not finance_file.exists() or not card_file.exists():
        print("Missing seed_data/*.txt files.", file=sys.stderr)
        sys.exit(1)

    with httpx.Client() as client:
        if args.agent_id:
            agent_id = args.agent_id
            print(f"Resuming agent_id={agent_id}")
            kb_items = _load_agent_kbs(client, token=token, agent_id=agent_id)
            vector_kb = _pick_kb(kb_items, storage_type="vector", name="Finance Policies")
            keyword_kb = _pick_kb(kb_items, storage_type="keyword", name="Card Management FAQ")
            print(f"  vector_kb_id={vector_kb['id']} status={vector_kb['status']}")
            print(f"  keyword_kb_id={keyword_kb['id']} status={keyword_kb['status']}")
        else:
            print("Creating orchestrator agent...")
            agent = _check_response(
                client.post(
                    f"{_api_base()}/agents",
                    headers={**_headers(token), "Content-Type": "application/json"},
                    json={
                        "name": "ABC Bank Assistant",
                        "description": "Payment, finance, and card management assistant with RAG and workflows.",
                        "industry": "financial_services",
                        "agent_type": "payment_collections",
                    },
                ),
                "create_agent",
            )
            agent_id = agent["id"]
            print(f"  agent_id={agent_id}")

            print("Creating vector KB (finance policies)...")
            vector_kb = create_knowledgebase(
                client,
                token=token,
                agent_id=agent_id,
                name="Finance Policies",
                storage_type="vector",
                file_path=finance_file,
                routing_hint="Search for loan EMI, savings, refunds, and payment plan policies",
            )
            print(f"  vector_kb_id={vector_kb['id']} status={vector_kb['status']}")

            print("Creating keyword KB (card management)...")
            keyword_kb = create_knowledgebase(
                client,
                token=token,
                agent_id=agent_id,
                name="Card Management FAQ",
                storage_type="keyword",
                file_path=card_file,
                routing_hint="Search for card activation, blocking, limits, PIN, and disputes",
            )
            print(f"  keyword_kb_id={keyword_kb['id']} status={keyword_kb['status']}")

        if args.sync_ingest:
            print("Running ingest synchronously...")
            asyncio.run(
                _run_sync_ingests(
                    kb_files=[(vector_kb, finance_file), (keyword_kb, card_file)],
                    agent_id=agent_id,
                )
            )

        print("Creating payment workflow...")
        workflow = _check_response(
            client.post(
                f"{_api_base()}/workflows",
                headers={**_headers(token), "Content-Type": "application/json"},
                json={
                    "name": "Make a Payment",
                    "description": "Guided payment amount collection workflow",
                    "agent_id": agent_id,
                    "routing_hint": "Start when the user wants to pay, make a payment, or set up a payment plan",
                    "nodes": PAYMENT_WORKFLOW_NODES,
                    "edges": PAYMENT_WORKFLOW_EDGES,
                },
            ),
            "create_workflow",
        )
        workflow_id = workflow["id"]
        print(f"  workflow_id={workflow_id}")

        print("Publishing workflow...")
        published = _check_response(
            client.post(
                f"{_api_base()}/workflows/{workflow_id}/publish",
                headers=_headers(token),
            ),
            "publish_workflow",
        )
        print(f"  workflow status={published['status']}")

        print("Creating finance_management sub-agent...")
        finance_sub = _check_response(
            client.post(
                f"{_api_base()}/agents/{agent_id}/sub-agents",
                headers={**_headers(token), "Content-Type": "application/json"},
                json={
                    "name": "finance_management",
                    "description": "Handles balances, EMIs, payment plans, and savings questions",
                    "instructions": (
                        "You are the finance specialist for ABC Bank. Answer questions about "
                        "loan EMIs, late fees, payment plans, savings interest, overdraft, and "
                        "refunds. Use search_knowledge on Finance Policies before answering. "
                        "Never ask for full card numbers or passwords."
                    ),
                    "knowledge_base_ids": [vector_kb["id"]],
                    "routing_hint": "Delegate for loan, EMI, savings, balance, refund, or payment plan questions",
                },
            ),
            "create_finance_sub_agent",
        )
        print(f"  finance_sub_agent_id={finance_sub['id']}")

        print("Creating card_management sub-agent...")
        card_sub = _check_response(
            client.post(
                f"{_api_base()}/agents/{agent_id}/sub-agents",
                headers={**_headers(token), "Content-Type": "application/json"},
                json={
                    "name": "card_management",
                    "description": "Handles debit/credit card activation, blocking, limits, and disputes",
                    "instructions": (
                        "You are the card management specialist for ABC Bank. Help with card "
                        "activation, lost/stolen blocking, credit limits, PIN reset, international "
                        "travel notices, and charge disputes. Use search_knowledge on Card "
                        "Management FAQ before answering."
                    ),
                    "knowledge_base_ids": [keyword_kb["id"]],
                    "routing_hint": "Delegate for card activation, block, PIN, limit, or dispute questions",
                },
            ),
            "create_card_sub_agent",
        )
        print(f"  card_sub_agent_id={card_sub['id']}")

        print("\n--- Seed complete ---")
        print(f"Agent ID:     {agent_id}")
        print(f"Vector KB:    {vector_kb['id']} (finance)")
        print(f"Keyword KB:   {keyword_kb['id']} (card)")
        print(f"Workflow ID:  {workflow_id} (published)")
        print(f"Sub-agents:   {finance_sub['id']}, {card_sub['id']}")
        print(f"\nPreview chat: POST {_api_base()}/agents/{agent_id}/preview/chat")
        print('Body: {"sender_id":"demo-user","message":"What is the late payment fee on my loan?"}')
        if not args.sync_ingest:
            print("\nNote: KB ingest runs via Celery. Re-run with --sync-ingest or wait for worker.")


if __name__ == "__main__":
    main()
