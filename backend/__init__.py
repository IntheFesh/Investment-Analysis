"""Backend package for the investment analysis platform.

This package groups together the FastAPI application, router modules, models and
services that power the REST API described in the project specification.  The
backend is deliberately lightweight and modular; each high‑level resource
(system, market, sentiment, portfolio, fund, simulation, import/export, settings)
has its own router with clearly defined endpoints.

The API schema follows the pattern described in the front‑end and back‑end
design document.  Responses include a success flag, message, data object and
metadata with timestamp and version.
"""

from .app import app  # noqa: F401