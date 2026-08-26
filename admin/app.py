from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from admin.auth import AuthRedirect
from admin import views
from admin.i18n import tr
from data import config

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def _tojson(value):
    return Markup(
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


templates.env.filters["tojson"] = _tojson


def create_panel(application) -> FastAPI:
    app = FastAPI(title="VolMafia Panel", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
    media = ROOT.parent / "data" / "media"
    (media / "shop").mkdir(parents=True, exist_ok=True)
    (media / "gifts").mkdir(parents=True, exist_ok=True)
    (media / "swaps").mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media)), name="media")
    app.state.tg = application
    app.state.templates = templates

    @app.middleware("http")
    async def _csrf(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if request.url.path.startswith("/api/market"):
                return await call_next(request)
            origin = request.headers.get("origin") or ""
            if origin:
                want = (request.headers.get("host") or "").lower()
                got = (urlparse(origin).netloc or "").lower()
                if want and got and got != want:
                    lang = request.cookies.get("panel_lang") or "uz"
                    return HTMLResponse(tr("csrf", lang), status_code=403)
        return await call_next(request)

    @app.exception_handler(AuthRedirect)
    async def _redir(_request: Request, exc: AuthRedirect):
        return RedirectResponse(exc.url, status_code=303)

    @app.exception_handler(Exception)
    async def _err(request: Request, exc: Exception):
        logger.exception("Panel xato: %s %s", request.method, request.url.path)
        lang = request.cookies.get("panel_lang") or "uz"
        return HTMLResponse(tr("panel_crash", lang), status_code=500)

    views.register(app)
    from admin import market as market_app

    market_app.register(app)
    return app


async def start_panel(application) -> None:
    web = create_panel(application)
    uv = uvicorn.Config(
        web,
        host=config.PANEL_HOST,
        port=config.PANEL_PORT,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(uv)
    server.install_signal_handlers = False
    application.bot_data["panel_server"] = server
    application.bot_data["panel_task"] = asyncio.create_task(
        server.serve(), name="admin-panel"
    )
    logger.info("Admin panel: http://%s:%s", config.PANEL_HOST, config.PANEL_PORT)


async def stop_panel(application) -> None:
    server = application.bot_data.get("panel_server")
    if server:
        server.should_exit = True
    task = application.bot_data.get("panel_task")
    if task:
        try:
            await asyncio.wait_for(task, timeout=4)
        except Exception:
            task.cancel()
