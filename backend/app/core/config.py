from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Constraining the value at the type level means a typo like ENVIRONMENT=prod
# fails at startup with a clear error, instead of silently running with
# "prod" and skipping every production-only branch in the codebase.
Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    """Every environment-specific value the app reads, in one typed object.

    BaseSettings reads from os.environ first, then falls back to the .env file.
    A value present in both wins in favour of the real environment variable, which
    is what lets a container override a committed .env at runtime.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # A stray variable in the environment (PATH, EDITOR, some tool's config)
        # should not crash startup. We only ever read the fields declared here.
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "WorkOS API"
    environment: Environment = "local"
    log_level: str = "INFO"

    # Note what is NOT here: the database URL, the JWT secret, CORS origins.
    # They are commented out in .env.example because they arrive in later
    # iterations. Any setting with no sensible default is declared without one,
    # so a missing value is a startup error rather than a surprise at 2am.
    #
    # Also note what is NOT configurable: the `/api/v1` path prefix. A URL prefix
    # is part of the API contract, not an environment detail - if staging and
    # production used different prefixes, our docs and frontend would be wrong in
    # one of them. Not everything belongs in config.


@lru_cache
def get_settings() -> Settings:
    """Return the single Settings instance.

    lru_cache means the .env file is parsed once per process, not once per request.
    FastAPI caches dependencies per-request, but this cache is process-wide, so
    every caller shares one object.
    """
    return Settings()
