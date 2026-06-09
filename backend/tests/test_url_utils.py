from app.shared.utils.url import safe_uri


def test_safe_uri_redacts_mongodb_credentials() -> None:
    uri = "mongodb://myuser:secretpass@cluster0.abc.mongodb.net/?retryWrites=true"
    assert safe_uri(uri) == "mongodb://***@cluster0.abc.mongodb.net/?retryWrites=true"


def test_safe_uri_redacts_srv_connection_string() -> None:
    uri = "mongodb+srv://myuser:secret@cluster0.abc.mongodb.net/"
    assert safe_uri(uri) == "mongodb+srv://***@cluster0.abc.mongodb.net/"


def test_safe_uri_returns_local_uri_unchanged() -> None:
    uri = "mongodb://localhost:27017"
    assert safe_uri(uri) == uri
