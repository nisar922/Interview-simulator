from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import os


def _fix_url(url: str) -> str:
    url = url.replace("postgres://", "postgresql+asyncpg://", 1).replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    if "sslmode" in query:
        query["ssl"] = query.pop("sslmode")
    query.pop("channel_binding", None)
    return urlunsplit(parts._replace(query=urlencode(query)))



DATABASE_URL = _fix_url(
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5434/interviews",
    )
)