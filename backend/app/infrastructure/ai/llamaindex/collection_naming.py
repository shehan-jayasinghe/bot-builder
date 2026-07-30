def kb_collection_name(*, organization_id: str, knowledgebase_id: str) -> str:
    return f"kb_{organization_id}_{knowledgebase_id}"
