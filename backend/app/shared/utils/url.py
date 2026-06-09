def safe_uri(uri: str) -> str:
    """Hide credentials in connection URLs for logs."""
    if "@" not in uri or "://" not in uri:
        return uri

    scheme, remainder = uri.split("://", 1)
    if "@" not in remainder:
        return uri

    _, host_part = remainder.split("@", 1)
    return f"{scheme}://***@{host_part}"
