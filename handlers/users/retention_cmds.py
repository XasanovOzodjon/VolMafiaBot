from __future__ import annotations

import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.common import store
from i18n import t


async def cmd_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    st = store(context)
    ok, status, data = await st.claim_daily_bonus(user.id)
    if ok:
        reward = data["reward"]
        streak = data["streak"]
        vip = data["vip"]
        vip_tag = " <i>(VIP 2x!)</i>" if vip else ""
        text = (
            f"🎁 <b>Kunlik bonus qabul qilindi!</b>\n\n"
            f"🔥 <b>Ketma-ketlik (Streak):</b> {streak}-kun\n"
            f"💰 <b>Mukofot:</b> +{reward['money']} ${vip_tag}\n"
        )
        if reward.get("vcoin", 0) > 0:
            text += f"💎 <b>Vcoin:</b> +{reward['vcoin']}{vip_tag}\n"
        if reward.get("protection", 0) > 0:
            text += f"🛡️ <b>Ximoya boosti:</b> +{reward['protection']}\n"
        text += "\n<i>Ertaga yana keling va bundan ham kattaroq bonusga ega bo‘ling!</i>"
        await message.reply_html(text)
    else:
        if status.startswith("wait_"):
            parts = status.split("_")
            h, m = parts[1], parts[2]
            await message.reply_html(
                f"⏳ <b>Bugungi bonusni allaqachon olgansiz!</b>\n\n"
                f"Keyingi bonusgacha: <b>{h} soat {m} daqiqa</b> qoldi."
            )
        else:
            await message.reply_html("❌ Hozircha bonus olib bo‘lmadi.")


async def cmd_box(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    st = store(context)
    stats = await st.get_stats(user.id)
    vcoin = int(stats.get("vcoin") or 0)
    if vcoin < 10:
        await message.reply_html(
            f"📦 <b>Omad Sandig‘i (Mafia Chest)</b>\n\n"
            f"Sandiq ochish narxi: <b>10 Vcoin</b>\n"
            f"Sizning balansingiz: <b>{vcoin} Vcoin</b>\n\n"
            f"❌ Vcoin yetarli emas! Sandiq ochish uchun do‘kondan Vcoin xarid qiling yoki o‘yinlarda yutib oling."
        )
        return

    ok, status, won = await st.open_lucky_box(user.id)
    if not ok:
        await message.reply_html("❌ Sandiq ochishda xatolik yuz berdi.")
        return

    text = (
        f"📦 <b>Sandiq ochildi!</b> ✨\n\n"
        f"🎉 <b>Yutug‘ingiz:</b> <b>{html.escape(won.get('text', 'Mukofot'))}</b>\n\n"
        f"<i>Omadingiz keldi! Yutuq hisobingizga qo‘shildi.</i>"
    )
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📦 Yana ochish (10 Vcoin)", callback_data="ret:box")]]
    )
    await message.reply_html(text, reply_markup=kb)


async def cmd_ref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return
    st = store(context)
    stats = await st.get_stats(user.id)
    me = await context.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{user.id}"

    count = int(stats.get("ref_count") or 0)
    earned = int(stats.get("ref_earnings") or 0)

    text = (
        f"👥 <b>Do‘stlarni taklif qilish (Referral)</b>\n\n"
        f"Sizning shaxsiy taklif havolangiz:\n"
        f"👉 <code>{ref_link}</code>\n\n"
        f"🎁 <b>Imtiyozlar:</b>\n"
        f"• Do‘stingiz taklif havolangizdan kirsa, darhol <b>25 $</b> sovg‘a oladi.\n"
        f"• Do‘stingiz birinchi o‘yinini o‘ynaganda sizga <b>40 $</b> va <b>2 Vcoin</b> beriladi!\n\n"
        f"📊 <b>Sizning statistikangiz:</b>\n"
        f"• Taklif qilingan do‘stlar: <b>{count} ta</b>\n"
        f"• Ishlangan pul: <b>{earned} $</b>"
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 Do‘stlarga ulashish",
                    url=f"https://t.me/share/url?url={ref_link}&text={html.escape('Biz bilan Mafia o‘yna! Havola orqali kirsang senga 25$ bonus beriladi!')}",
                )
            ]
        ]
    )
    await message.reply_html(text, reply_markup=kb)


async def on_retention_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    data = query.data
    if data == "ret:bonus":
        await cmd_bonus(update, context)
    elif data == "ret:box":
        await cmd_box(update, context)
    elif data == "ret:ref":
        await cmd_ref(update, context)
