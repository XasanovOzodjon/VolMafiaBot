from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import urllib.error
import urllib.request
from typing import Optional

from data import config

logger = logging.getLogger(__name__)

_proc: Optional[asyncio.subprocess.Process] = None
_web = "127.0.0.1:4040"


async def _port_open(host: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        return True
    except OSError:
        return False


async def _wait_local_port(port: int, timeout: float = 12) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if await _port_open("127.0.0.1", port):
            return True
        await asyncio.sleep(0.15)
    return False


def _pick_url(data: dict) -> str:
    for tunnel in data.get("tunnels") or []:
        url = str(tunnel.get("public_url") or "").rstrip("/")
        if url.startswith("https://"):
            return url
    for endpoint in data.get("endpoints") or []:
        url = str(endpoint.get("url") or "").rstrip("/")
        if url.startswith("https://"):
            return url
    return ""


def _read_https_url(web: str) -> str:
    headers = {"User-Agent": "VolMafiaBot"}
    for path in ("/api/tunnels", "/api/endpoints"):
        req = urllib.request.Request(f"http://{web}{path}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            continue
        url = _pick_url(data if isinstance(data, dict) else {})
        if url:
            return url
    return ""


async def _existing_https_url(web: str) -> str:
    try:
        return await asyncio.to_thread(_read_https_url, web)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return ""


async def start_debug_tunnel(port: int) -> str:
    """DEBUG rejimida ngrok HTTPS tunnel. Productionda chaqirilmasin."""
    global _proc, _web
    if not await _wait_local_port(port):
        logger.error("Panel %s portda ochilmadi, ngrok ishlamaydi.", port)
        return ""
    for web in ("127.0.0.1:4040", "127.0.0.1:4045"):
        existing = await _existing_https_url(web)
        if existing:
            _web = web
            config.set_public_url(existing)
            logger.info("DEBUG Mini App (ngrok): %s", existing)
            return existing
    await stop_debug_tunnel()
    ngrok = shutil.which("ngrok")
    if not ngrok:
        logger.error("ngrok topilmadi. brew install ngrok yoki https://ngrok.com")
        return ""
    web = "127.0.0.1:4040"
    if await _port_open("127.0.0.1", 4040):
        web = "127.0.0.1:4045"
        if await _port_open("127.0.0.1", 4045):
            logger.error("ngrok web UI 4040/4045 band.")
            return ""
    _web = web
    env = os.environ.copy()
    env["NGROK_WEB_ADDR"] = web
    try:
        _proc = await asyncio.create_subprocess_exec(
            ngrok,
            "http",
            f"127.0.0.1:{port}",
            "--host-header=rewrite",
            env=env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.error("ngrok topilmadi. brew install ngrok yoki https://ngrok.com")
        return ""
    deadline = asyncio.get_event_loop().time() + 20
    while asyncio.get_event_loop().time() < deadline:
        if _proc.returncode is not None:
            logger.error("ngrok chiqib ketdi, kod=%s", _proc.returncode)
            _proc = None
            return ""
        url = await _existing_https_url(web)
        if url:
            config.set_public_url(url)
            logger.info("DEBUG Mini App (ngrok): %s", url)
            return url
        await asyncio.sleep(0.3)
    logger.error("ngrok HTTPS manzil kelmadi. ngrok login / authtoken tekshiring.")
    await stop_debug_tunnel()
    return ""


async def stop_debug_tunnel() -> None:
    global _proc
    if _proc is None:
        return
    proc = _proc
    _proc = None
    if proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=3)
        except Exception:
            proc.kill()
            try:
                await proc.wait()
            except Exception:
                pass
