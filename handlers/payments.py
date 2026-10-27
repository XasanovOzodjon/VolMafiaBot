from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import store
from i18n import t


async def on_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if not query:
        return
    payload = str(query.invoice_payload or "")
    ok = payload.startswith("vcoin:") or payload.startswith("money:")
    await query.answer(ok=ok)


async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.successful_payment:
        return
    pay = message.successful_payment
    payload = str(pay.invoice_payload or "")
    parts = payload.split(":")
    if len(parts) < 4 or parts[0] not in ("vcoin", "money"):
        return
    kind, pack_id, want_amount, want_stars = parts[0], parts[1], parts[2], parts[3]
    try:
        amount = int(want_amount)
        stars = int(want_stars)
    except ValueError:
        return
    if int(pay.total_amount or 0) != stars or amount <= 0:
        return
    st = store(context)
    if await st.stars_paid(pay.telegram_payment_charge_id):
        return
    pack = await st.vcoin_pack(pack_id)
    if pack:
        pack_kind = str(pack.get("kind") or kind)
        if pack_kind == "money":
            amount = int(pack.get("money") or amount)
        else:
            amount = int(pack.get("vcoin") or amount)
        kind = pack_kind if pack_kind in ("vcoin", "money") else kind
    lang = await st.get_user_lang(user.id)
    detail = f"{pack_id}:{pay.telegram_payment_charge_id}"
    if kind == "money":
        await st.credit_money(user.id, amount, kind="stars", detail=detail)
        await message.reply_html(t("stars_ok_money", lang, n=amount))
        return
    await st.credit_vcoin(user.id, amount, kind="stars", detail=detail)
    await message.reply_html(t("stars_ok", lang, n=amount))
