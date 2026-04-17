"""Backend-owned analytics layer.

All quantitative/financial computation lives here, not in the frontend and
not scattered across routers. Each submodule is deterministic given the
adapter's data snapshot, which keeps output stable across page loads.
"""
