from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.core.config import settings
from app.core.observability import scrub_event
from app.core.rls import warn_if_rls_dormant
from app.core.storage import ensure_bucket
from app.shared.errors import ErrorResponse, register_exception_handlers


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        before_send=scrub_event,
        before_send_transaction=scrub_event,
        # Don't ship exception frame locals: verify_token/get_bearer_token hold
        # the raw JWT in a local, which would otherwise leak on any uncaught
        # error (frame locals are captured independently of send_default_pii).
        include_local_variables=False,
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_bucket(settings.MINIO_DEFAULT_BUCKET)
    if settings.OCR_ENABLED:
        ensure_bucket(settings.OCR_BUCKET)
    warn_if_rls_dormant()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

register_exception_handlers(app)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(
    v1_router,
    prefix=settings.API_V1_STR,
    responses={"4XX": {"model": ErrorResponse}},
)


def custom_openapi() -> dict[str, Any]:
    """OpenAPI schema with error responses using the §3.6 envelope.

    FastAPI hardcodes ``HTTPValidationError`` as the 422 response model;
    alias it to ``ErrorResponse`` so generated clients type every error
    response as the standard envelope.
    """
    if app.openapi_schema:
        return app.openapi_schema
    schema = original_openapi()
    schemas = schema.get("components", {}).get("schemas", {})
    if "HTTPValidationError" in schemas and "ErrorResponse" in schemas:
        schemas["HTTPValidationError"] = {"$ref": "#/components/schemas/ErrorResponse"}
        schemas.pop("ValidationError", None)
    app.openapi_schema = schema
    return schema


original_openapi = app.openapi
app.openapi = custom_openapi  # type: ignore[method-assign]  # ty: ignore[invalid-assignment]

if settings.AI_ENABLED:
    from app.modules.ai.copilotkit import setup_copilotkit

    setup_copilotkit(app)
