class RAGRetriever:
    async def retrieve(self, *, query: str, knowledge_base_ids: list[str]) -> str:
        """
        Retrieve relevant context for the user query.

        TODO:
          - Qdrant vector search
          - Bedrock Titan embeddings
          - emit trace event: rag_complete
        """
        _ = query, knowledge_base_ids
        return ""
