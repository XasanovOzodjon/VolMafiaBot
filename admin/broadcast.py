from __future__ import annotations

import asyncio
import json
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.error import Forbidden, RetryAfter, TelegramError


def parse_buttons(raw: str) -> list:
    """Legacy: 'Matn | https://...' per line. Also accepts JSON rows."""
    text = (raw or "").strip()
    if not text:
        return []
    if text[:1] in "[{":
        try:
            return normalize_buttons(json.loads(text))
        except json.JSONDecodeError:
            pass
    buttons = []
    for line in text.splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        label, url = line.split("|", 1)
        label, url = label.strip(), url.strip()
        if label and url.startswith("http"):
            buttons.append({"text": label, "url": url})
    return [[b] for b in buttons[:8]]


def normalize_buttons(data) -> list[list[dict]]:
    if not data:
        return []
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        rows = []
        for b in data:
            t, u = (b.get("text") or "").strip(), (b.get("url") or "").strip()
            if t and u.startswith("http"):
                rows.append([{"text": t[:64], "url": u}])
        return rows[:8]
    rows: list[list[dict]] = []
    if not isinstance(data, list):
        return []
    for row in data:
        if not isinstance(row, list):
            continue
        cells = []
        for b in row:
            if not isinstance(b, dict):
                continue
            t, u = (b.get("text") or "").strip(), (b.get("url") or "").strip()
            if t and u.startswith("http"):
                cells.append({"text": t[:64], "url": u})
        if cells:
            rows.append(cells[:8])
        if len(rows) >= 8:
            break
    return rows


def ad_media_list(ad: dict) -> list[dict]:
    """Normalize 1–10 Telegram media items. Album = photo/video only."""
    raw = ad.get("media_items")
    out: list[dict] = []
    if isinstance(raw, list):
        for it in raw:
            if not isinstance(it, dict):
                continue
            fid = str(it.get("file_id") or "").strip()
            kind = str(it.get("type") or it.get("media_type") or "photo")
            if kind not in ("photo", "video", "animation"):
                kind = "photo"
            if fid:
                out.append({"type": kind, "file_id": fid})
            if len(out) >= 10:
                break
    if out:
        return out
    fid = str(ad.get("file_id") or "").strip()
    kind = str(ad.get("media_type") or "none")
    if not fid or kind in ("", "none"):
        return []
    if kind == "album":
        kind = "photo"
    if kind not in ("photo", "video", "animation"):
        kind = "photo"
    return [{"type": kind, "file_id": fid}]


def markup_from_ad(ad: dict) -> InlineKeyboardMarkup | None:
    rows = []
    for row in normalize_buttons(ad.get("buttons") or []):
        rows.append([InlineKeyboardButton(b["text"], url=b["url"]) for b in row])
    return InlineKeyboardMarkup(rows) if rows else None


def ad_lang_mode(ad: dict) -> str:
    mode = ad.get("lang_mode")
    if mode in ("single", "multi"):
        return mode
    if (ad.get("text_ru") or "").strip() or (ad.get("text_en") or "").strip():
        return "multi"
    return "single"


def ad_texts(ad: dict) -> dict[str, str]:
    uz = (ad.get("text_uz") or ad.get("text") or "").strip()
    ru = (ad.get("text_ru") or "").strip()
    en = (ad.get("text_en") or "").strip()
    return {"uz": uz, "ru": ru, "en": en}


def pick_ad_text(ad: dict, lang: str | None) -> str:
    texts = ad_texts(ad)
    if ad_lang_mode(ad) != "multi":
        return texts["uz"] or texts["ru"] or texts["en"]
    code = str(lang or "uz").lower()
    if code.startswith("ru"):
        return texts["ru"] or texts["uz"] or texts["en"]
    if code.startswith("en"):
        return texts["en"] or texts["uz"] or texts["ru"]
    return texts["uz"] or texts["ru"] or texts["en"]


async def ad_text_for(store, chat_id: int, ad: dict) -> str:
    if ad_lang_mode(ad) != "multi" or store is None:
        return pick_ad_text(ad, "uz")
    try:
        if chat_id > 0:
            lang = await store.get_user_lang(chat_id)
        else:
            lang = await store.get_chat_lang(chat_id)
    except Exception:
        lang = "uz"
    return pick_ad_text(ad, lang)


async def _send_kb(bot, chat_id: int, kb, silent: bool) -> None:
    if not kb:
        return
    try:
        await bot.send_message(
            chat_id,
            "\u2060",
            reply_markup=kb,
            disable_notification=silent,
        )
    except TelegramError:
        pass


async def send_ad_to(bot, chat_id: int, ad: dict, store=None) -> bool:
    text = await ad_text_for(store, chat_id, ad)
    kb = markup_from_ad(ad)
    items = ad_media_list(ad)
    album = [it for it in items if it["type"] in ("photo", "video")]
    silent = bool(ad.get("silent"))
    preview = bool(ad.get("link_preview"))
    extra = {"parse_mode": "HTML", "reply_markup": kb, "disable_notification": silent}
    try:
        msg = None
        if len(album) >= 2:
            group = []
            for i, it in enumerate(album[:10]):
                cap = {"caption": text, "parse_mode": "HTML"} if i == 0 and text else {}
                if it["type"] == "video":
                    group.append(InputMediaVideo(media=it["file_id"], **cap))
                else:
                    group.append(InputMediaPhoto(media=it["file_id"], **cap))
            msgs = await bot.send_media_group(
                chat_id, media=group, disable_notification=silent
            )
            msg = msgs[0] if msgs else None
            await _send_kb(bot, chat_id, kb, silent)
        elif items:
            it = items[0]
            kind, file_id = it["type"], it["file_id"]
            if kind == "photo":
                msg = await bot.send_photo(chat_id, file_id, caption=text or None, **extra)
            elif kind == "animation":
                msg = await bot.send_animation(chat_id, file_id, caption=text or None, **extra)
            elif kind == "video":
                msg = await bot.send_video(chat_id, file_id, caption=text or None, **extra)
            else:
                msg = await bot.send_photo(chat_id, file_id, caption=text or None, **extra)
        else:
            if not text:
                return False
            msg = await bot.send_message(
                chat_id,
                text,
                disable_web_page_preview=not preview,
                **extra,
            )
        if ad.get("pin") and chat_id < 0 and msg:
            try:
                await bot.pin_chat_message(
                    chat_id, msg.message_id, disable_notification=True
                )
            except TelegramError:
                pass
        return True
    except RetryAfter as exc:
        await asyncio.sleep(float(exc.retry_after) + 0.4)
        return await send_ad_to(bot, chat_id, ad, store=store)
    except (Forbidden, TelegramError):
        return False


async def collect_targets(store, ad: dict) -> list[int]:
    kind = ad.get("target") or "all_users"
    if kind == "all_users":
        raw = await store.redis.smembers("mafia:players")
        out = []
        for uid in raw:
            n = int(uid)
            if not await store.is_user_banned(n):
                out.append(n)
        return out
    if kind == "all_groups":
        ids = []
        for g in await store.list_groups():
            if g.get("left") or await store.is_group_banned(int(g["id"])):
                continue
            ids.append(int(g["id"]))
        return ids
    return [int(x) for x in (ad.get("ids") or [])]


async def run_broadcast(application, ad_id: str) -> None:
    store = application.bot_data["store"]
    ad = await store.get_ad(ad_id)
    if not ad:
        return
    ad["status"] = "sending"
    ad["started_at"] = int(time.time())
    await store.save_ad(ad)
    targets = await collect_targets(store, ad)
    ok = fail = 0
    total = len(targets)
    ad["stats"] = {"ok": 0, "fail": 0, "total": total}
    await store.save_ad(ad)
    for chat_id in targets:
        fresh = await store.get_ad(ad_id)
        if fresh and fresh.get("status") == "cancelled":
            return
        if await send_ad_to(application.bot, chat_id, ad, store=store):
            ok += 1
        else:
            fail += 1
        if (ok + fail) % 3 == 0 or (ok + fail) == total:
            ad["stats"] = {"ok": ok, "fail": fail, "total": total}
            await store.save_ad(ad)
        await asyncio.sleep(0.05)
    ad["status"] = "sent"
    ad["stats"] = {"ok": ok, "fail": fail, "total": total}
    ad["finished_at"] = int(time.time())
    await store.save_ad(ad)
    await store.bump_metric("ads", 1)


async def broadcast_job(context) -> None:
    await run_broadcast(context.application, context.job.data)


def schedule_ad(application, ad: dict) -> None:
    jq = application.job_queue
    if not jq:
        return
    name = f"ad:{ad['id']}"
    for job in jq.get_jobs_by_name(name):
        job.schedule_removal()
    send_at = int(ad.get("send_at") or 0)
    now = int(time.time())
    delay = max(1.0, float(send_at - now)) if send_at > now else 1.0
    jq.run_once(broadcast_job, when=delay, data=ad["id"], name=name)


async def reschedule_ads(application) -> None:
    store = application.bot_data["store"]
    now = int(time.time())
    for ad in await store.list_ads(100):
        status = ad.get("status")
        send_at = int(ad.get("send_at") or 0)
        if status == "sending":
            schedule_ad(application, {**ad, "send_at": now + 2})
        elif status == "scheduled" and send_at > now:
            schedule_ad(application, ad)
