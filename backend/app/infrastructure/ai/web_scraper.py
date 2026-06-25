import logging

from langchain_community.document_loaders import RecursiveUrlLoader

from app.domain.models.source_document import SourceDocument

logger = logging.getLogger(__name__)


def scrape_website(*, website_url: str, crawl_depth: int) -> list[SourceDocument]:
    loader = RecursiveUrlLoader(
        url=website_url,
        max_depth=crawl_depth,
        prevent_outside=True,
        use_async=False,
        timeout=30,
    )
    documents = loader.load()
    if not documents:
        raise ValueError(f"No content scraped from {website_url}")

    results: list[SourceDocument] = []
    for document in documents:
        text = (document.page_content or "").strip()
        if not text:
            continue
        metadata = dict(document.metadata or {})
        metadata.setdefault("url", metadata.get("source", website_url))
        results.append(SourceDocument(text=text, metadata=metadata))

    if not results:
        raise ValueError(f"No usable text scraped from {website_url}")

    logger.info("Scraped %s pages from %s", len(results), website_url)
    return results
