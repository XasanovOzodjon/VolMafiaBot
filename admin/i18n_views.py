from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from i18n import admin as i18n_admin
from i18n.cache import cache, reload_all_cache
from i18n.seed import flag_for


def _groups(keys: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for key in keys:
        prefix = key.split("_", 1)[0] if "_" in key else key
        grouped.setdefault(prefix, []).append(key)
    return grouped


def register(app: FastAPI) -> None:
    from admin.views import _audit, _html, _need

    @app.get("/i18n", response_class=HTMLResponse)
    async def i18n_home(request: Request):
        sess = await _need(request, "settings")
        langs = cache.languages()
        for row in langs:
            row["flag"] = flag_for(row["code"])
        return _html(request, "i18n_langs.html", sess, langs=langs)

    @app.post("/i18n/add")
    async def i18n_add(
        request: Request,
        code: str = Form(...),
        name: str = Form(""),
        template: str = Form("uz"),
        private: str = Form(""),
    ):
        await _need(request, "settings")
        err = await i18n_admin.add_language(code, name, template, private=bool(private))
        if err != "ok":
            return RedirectResponse(f"/i18n?err={err}", 303)
        await _audit(request, "i18n_add", lang=code)
        return RedirectResponse(f"/i18n/{code.strip().lower()}/edit?ok=saved", 303)

    @app.post("/i18n/{code}/active")
    async def i18n_active(request: Request, code: str, on: int = Form(1)):
        await _need(request, "settings")
        await i18n_admin.set_active(code, bool(on))
        await _audit(request, "i18n_active", lang=code)
        return RedirectResponse("/i18n?ok=saved", 303)

    @app.post("/i18n/{code}/private")
    async def i18n_private(request: Request, code: str, on: int = Form(1)):
        await _need(request, "settings")
        await i18n_admin.set_private(code, bool(on))
        await _audit(request, "i18n_private", lang=code)
        return RedirectResponse("/i18n?ok=saved", 303)

    @app.get("/i18n/{code}/edit", response_class=HTMLResponse)
    async def i18n_edit(request: Request, code: str, q: str = ""):
        sess = await _need(request, "settings")
        lang = await i18n_admin.language_or_none(code)
        if not lang:
            return RedirectResponse("/i18n?err=missing", 303)
        texts = await i18n_admin.texts_for(code)
        keys = await i18n_admin.all_keys()
        qn = (q or "").strip().lower()
        if qn:
            keys = [k for k in keys if qn in k.lower() or qn in (texts.get(k) or "").lower()]
        return _html(
            request,
            "i18n_edit.html",
            sess,
            lang=lang,
            texts=texts,
            keys=keys,
            groups=_groups(keys),
            q=q,
            flag=flag_for(code),
            langs=cache.languages(),
        )

    @app.post("/i18n/{code}/save")
    async def i18n_save(request: Request, code: str):
        await _need(request, "settings")
        form = await request.form()
        mapping = {
            k[2:]: str(v)
            for k, v in form.items()
            if str(k).startswith("k:")
        }
        await i18n_admin.save_texts(code, mapping)
        await reload_all_cache()
        await _audit(request, "i18n_save", lang=code)
        return RedirectResponse(f"/i18n/{code}/edit?ok=saved", 303)
