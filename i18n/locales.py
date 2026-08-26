from __future__ import annotations

DEFAULT_LANG = "uz"
SUPPORTED = ("uz", "ru", "en")

LANG_FLAGS = {
    "uz": "🇺🇿",
    "ru": "🇷🇺",
    "en": "🇬🇧",
}


def normalize(lang: str | None) -> str:
    from i18n.cache import cache

    if cache.memory:
        return cache.normalize(lang)
    if lang in SUPPORTED:
        return lang
    return DEFAULT_LANG


def t(key: str, lang: str | None = None, **kwargs) -> str:
    from i18n.cache import cache

    code = normalize(lang)
    text = cache.get(code, key) if cache.memory else None
    if not text:
        table = TEXTS.get(code) or TEXTS[DEFAULT_LANG]
        text = table.get(key) or TEXTS[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return text
    return text


TEXTS: dict[str, dict[str, str]] = {
    "uz": {
        "start": "Salom!\nMen 🤵🏻 Mafia o'yinini rasmiy botiman.",
        "btn_add_group": "🤵🏻 Botni guruhga qo'shish ↗️",
        "btn_join_group": "🎲 Guruhga kirish",
        "btn_language": "🇺🇿 Til / Language",
        "btn_profile": "👤 Profil",
        "btn_roles": "🎭 Rollar",
        "btn_stats": "📊 Statistika",
        "btn_rating": "🏆 Reyting",
        "btn_close": "❌ Yopish",
        "btn_shop": "🛒 Do'kon",
        "btn_market": "🎁 Market",
        "btn_profile_app": "👤 Profil",
        "btn_topup": "💳 To'ldirish",
        "btn_buy_money": "Sotib olish 💵",
        "btn_buy_gems": "Sotib olish 🪙",
        "btn_buy_vcoin": "Sotib olish 🪙",
        "btn_use": "✅ Ishlatish",
        "btn_armed": "⏳ Keyingi o'yin",
        "btn_pick_role": "🎭 Rol tanlash",
        "btn_stars": "⭐ Vcoin",
        "shop_soon": "Do'kon tez orada.",
        "shop_title": "<b>Do'kon</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_header": "<b>Do'kon</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_item_line": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_item_card": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_price_money": "💵 {n}",
        "shop_price_vcoin": "🪙 {n}",
        "shop_empty": "Hozir mahsulot yo'q.",
        "shop_bought": "Sotib olindi: {item}",
        "shop_broke": "Mablag' yetarli emas.",
        "shop_missing": "Mahsulot topilmadi.",
        "shop_off": "Bu mahsulot o'chirilgan.",
        "shop_no_price": "Bu mahsulot uchun narx yo'q.",
        "shop_used": "Keyingi o'yinda ishlatiladi: {item}",
        "shop_already": "Allaqachon keyingi o'yinga qo'yilgan.",
        "shop_need_item": "Avval sotib oling.",
        "shop_need_pick": "Avval rol tanlang.",
        "shop_role_saved": "Tanlangan rol: {role}",
        "shop_pick_title": "Qaysi rolni olishni xohlaysiz?",
        "shop_armed_line": "Keyingi o'yin: {items}",
        "shop_pick_now": "Tanlangan: {role}",
        "role_active_public": "🎎 Faol rol",
        "protect_fired": "Kimnidir ximoyasi ishga tushdi!",
        "stars_title": "<b>Vcoin paketlar</b>\nTelegram Stars evaziga.",
        "stars_invoice": "{n} Vcoin",
        "stars_desc": "VolMafia Vcoin",
        "stars_ok": "+{n} Vcoin qo'shildi.",
        "stars_off": "Stars to'lov hozir ishlamayapti. PANEL_PUBLIC_URL / bot sozlamalarini tekshiring.",
        "gift_ok": "Buyurtma qabul qilindi. Admin siz bilan bog'lanadi.",
        "gift_broke": "Vcoin yetarli emas.",
        "gift_missing": "Sovg'a topilmadi.",
        "gift_busy": "Avvalgi buyurtmalar bajarilishini kuting.",
        "shop_boost_fail_chosen": "Tanlangan rol shu o'yinda joy topilmadi. Zaryad saqlanib qoldi.",
        "shop_boost_fail_active": "Faol rol shu o'yinda berilmadi. Zaryad saqlanib qoldi.",
        "gift_done_dm": "🎁 Buyurtmangiz bajarildi: {title}",
        "gift_cancel_dm": "🎁 Buyurtma bekor. 🪙 {n} Vcoin qaytarildi.",
        "gift_admin": "🎁 Yangi buyurtma #{id}\n{name} (<code>{uid}</code>) {user}\n{emoji} {title}\n🪙 {vcoin}",
        "market_need_https": "Mini App Market uchun PANEL_PUBLIC_URL HTTPS bo'lishi kerak.",
        "market_tab_gifts": "🎁 Sovg'alar",
        "market_tab_boosts": "🎎 O'yin",
        "market_tab_stars": "⭐ Vcoin",
        "market_tab_swap": "💵 $",
        "market_empty_gifts": "Hozir ochiq sovg'a yo'q.",
        "market_empty_shop": "Mahsulot yo'q.",
        "market_empty_packs": "Paket yo'q.",
        "market_empty_swap": "Almashuv yo'q.",
        "market_confirm_gift": "{title} uchun {n} Vcoin yozasizmi? Admin qo'lda yuboradi.",
        "market_confirm_swap": "{v} Vcoin ni {m}$ ga almashtirasizmi?",
        "market_swap": "Almashtirish",
        "market_swap_ok": "+{m}$ · −{v} Vcoin",
        "market_swap_hint": "Vcoin ni oddiy $ ga almashtirish. To'ldirish alohida.",
        "market_auth": "Marketni Telegram Mini App orqali oching.",
        "market_error": "Xato. Qayta urinib ko'ring.",
        "market_bought": "Sotib olindi.",
        "market_used": "Keyingi o'yinga qo'yildi.",
        "market_add": "Qo'shish",
        "market_buy": "Sotib olish",
        "market_close": "Yopish",
        "app_profile": "Profil",
        "app_topup": "To'ldirish",
        "topup_pick": "To'lov usulini tanlang",
        "topup_kind": "Nimani to'ldirasiz?",
        "pay_stars": "⭐ Telegram Stars",
        "pay_stars_desc": "Vcoin ni Telegram Stars bilan oling.",
        "pay_market": "🎁 Market",
        "pay_market_desc": "Market orqali ham hisobni to'ldirish mumkin.",
        "pay_vcoin": "🪙 Vcoin",
        "pay_vcoin_desc": "Telegram Stars evaziga Vcoin oling.",
        "pay_money": "💵 Pul ($)",
        "pay_money_desc": "Telegram Stars evaziga $ oling.",
        "profile_games": "O'yinlar",
        "profile_wins": "G'alaba",
        "profile_inv": "Inventar",
        "profile_empty_inv": "Inventar bo'sh.",
        "profile_badges": "Badge",
        "profile_badges_empty": "Hali Badge yo'q.",
        "topup_hint": "Usulni tanlang, keyin paketni bosing.",
        "topup_hint_kind": "Avval Vcoin yoki $ ni tanlang, keyin paketni bosing.",
        "stars_ok_money": "+{n}$ qo'shildi.",
        "stars_invoice_money": "{n}$",
        "stars_desc_money": "VolMafia $",
        "maintenance": "Bot hozir texnik tanaffusda. Keyinroq urinib ko'ring.",
        "user_banned": "Siz o'yin o'ynay olmaysiz.",
        "group_banned": "Bu guruhda o'yin o'ynash taqiqlangan.",
        "join_banned": "Siz bloklangansiz.",
        "staff_not_super": "Faqat super-admin.",
        "staff_wait": "User ID yuboring yoki xabarni forward qiling.",
        "staff_need_user": "User ID yoki reply kerak.",
        "staff_pick": "{name} (<code>{id}</code>) uchun rol tanlang.",
        "staff_added": "Shtabga qo'shildi: <code>{id}</code> — {role}",
        "staff_removed": "Shtabdan olindi: <code>{id}</code>",
        "staff_env": "ENV adminni olib tashlab bo'lmaydi.",
        "staff_cancelled": "Bekor qilindi.",
        "staff_only": "Bu bo'lim faqat adminlar uchun.",
        "staff_role_super": "👑 Super",
        "staff_role_moderator": "🛡️ Moderator",
        "staff_role_ads": "📣 Ads",
        "btn_back": "🔙 Ortga",
        "roles_title": "<b>Mavjud rollar ro'yxati</b>\nUning tavsifini ko'rish uchun rol nomini bosing",
        "lang_title": "Tilni tanlang / Choose language:",
        "lang_pick_first": (
            "🌐 Tilni tanlang\n"
            "Выберите язык\n"
            "Choose language"
        ),
        "lang_uz": "🇺🇿 O'zbekcha",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "lang_saved": "Til o'zgartirildi: O'zbekcha",
        "profile_text": (
            "👤 {username}\n"
            "💵 Pullar: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Ximoya: {protection}\n"
            "📁 Hujjatlar: {documents}\n"
            "🎎 Faol rol: {active_role}\n"
            "🎭 Tanlangan rol: {chosen_role}"
        ),
        "profile_body": (
            "👤 {username}\n"
            "💵 Pullar: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Ximoya: {protection}\n"
            "📁 Hujjatlar: {documents}\n"
            "🎎 Faol rol: {active_role}\n"
            "🎭 Tanlangan rol: {chosen_role}"
        ),
        "profile_win_header": (
            "<b>O'yin tugadi</b>\n"
            "\"{role}\" rolida yutganingiz uchun sizga 💵 {amount} berildi!"
        ),
        "profile_reward_header": (
            "<b>O'yin tugadi</b>\n"
            "\"{role}\" roli uchun sizga 💵 {amount} berildi!"
        ),
        "group_settings": (
            "⚙️ <b>Guruh sozlamalari</b>\n\n"
            "🌐 Til: {lang_name}\n"
            "▶️ Auto-start: {auto}"
        ),
        "group_lang_admin": "Tilni faqat guruh admini o'zgartira oladi.",
        "group_settings_admin": "Sozlamalarni faqat guruh admini o'zgartira oladi.",
        "auto_on": "yoqilgan",
        "auto_off": "o'chirilgan",
        "auto_enabled": "Auto-start yoqildi.",
        "auto_disabled": "Auto-start o'chirildi.",
        "btn_auto_on": "✅ Auto-start: yoqilgan",
        "btn_auto_off": "❌ Auto-start: o'chirilgan",
        "reg_wait_start": "⏳ Ro'yxat vaqti tugadi. Auto-start o'chirilgan — o'yinni /start bilan boshlang.",
        "no_group_link": "O'yin guruhi havolasi hali sozlanmagan.",
        "help_private": (
            "🎭 Men guruhdagi <b>Mafia</b> o'yinini olib boraman.\n\n"
            "1) Botni guruhga qo'shing va <b>admin</b> qiling.\n"
            "2) Guruhda /game yozing.\n"
            "3) Avval shu yerga /start bosing, keyin qo'shiling.\n"
            "4) 🛒 Do'kon — ximoya/hujjat ($), faol/tanlangan rol (Vcoin).\n"
            "5) 🎁 Market — Vcoin evaziga real sovg'alar."
        ),
        "help_group": (
            "🎭 <b>Buyruqlar</b>\n"
            "/game — ro'yxatni ochish\n"
            "/start — o'yinni boshlash\n"
            "/extend — ro'yxatni uzaytirish\n"
            "/stop — o'yinni to'xtatish\n"
            "/exit — o'zingizni o'ldirish\n"
            "/game-test N — test (botlar, faqat admin)\n"
            "/settings — guruh sozlamalari\n"
            "/qoidalar — rollar"
        ),
        "btn_join": "✅ Qo'shilish",
        "join_ok": "Siz o'yinga omadli qo'shildingiz {group}",
        "join_already": "Sabr qiling siz o'yindasiz! Tushunyapsizmi? O'yinda! :)",
        "join_closed": "Hozir ro'yxat yopiq.",
        "join_full": "Joy qolmadi.",
        "join_other": "Siz boshqa o'yindasiz.",
        "join_not_found": "O'yin topilmadi. Guruhda /game yozing.",
        "btn_leave": "❌ Chiqish",
        "btn_start_game": "▶️ O'yinni boshlash",
        "btn_group_lang": "🌐 Til",
        "reg_already": "Ro'yxatdan o'tish allaqachon ketmoqda.",
        "game_already": "Bu guruhda o'yin allaqachon davom etmoqda.",
        "test_usage": (
            "🧪 Test: <code>/game-test 8</code>\n"
            "Ro'yxat originaldek. N — jami o'yinchilar (odamlar + botlar), {min}–{max}."
        ),
        "test_admin_only": "Test rejimini faqat guruh admini yoki bot admini yoqishi mumkin.",
        "test_pick_role": (
            "🧪 <b>Test rejim</b>\n"
            "O'yinchilar: <b>{n}</b> (siz + {bots} bot)\n\n"
            "O'zingizga rol tanlang. Qolgan rollar botlarga tasodifiy beriladi.\n"
            "Botlar ruscha o'ynaydi. Statistika yozilmaydi."
        ),
        "test_pick_role_dm": (
            "🧪 <b>Test.</b> O'zingizga rol tanlang.\n"
            "Bu tanlov faqat sizga ko'rinadi. O'yin boshlanmaguncha o'zgartirishingiz mumkin.\n"
            "Tanlamasangiz, start paytida tasodifiy rol beriladi."
        ),
        "test_role_picked": (
            "🧪 Siz {role} ni tanladingiz.\n"
            "O'yin boshlanmaguncha tugmadan boshqasini bosib o'zgartirishingiz mumkin."
        ),
        "test_role_taken": "Bu rol band. Boshqasini tanlang.",
        "test_started": (
            "🧪 <b>Test boshlandi.</b> Odamlar: {humans}, botlar: {bots}.\n"
            "Botlar guruhda ruscha gaplashadi va tunda/ovozda o'zlari yurish qiladi. Statistika yozilmaydi."
        ),
        "test_setup_timeout": "🧪 Test bekor qilindi — rol tanlanmadi.",
        "test_not_setup": "Hozir test rolini tanlash emas.",
        "test_only_host": "Rolni faqat testni boshlagan odam tanlaydi.",
        "test_pick_pending": "Avval test uchun rol tanlang yoki /stop qiling.",
        "test_reg_text": (
            "🧪 <b>Test Mafia</b>\n\n"
            "Ro'yxatdan o'tish ochiq (asl o'yindek).\n"
            "Odamlar: <b>{n}/{max}</b>\n"
            "Startida qo'shiladigan botlar: <b>{bots}</b>\n\n"
            "Rolni bot lichkasida tanlang — bu shaxsiy.\n\n"
            "{players}"
        ),
        "reg_text": (
            "🎭 <b>Mafia o'yini</b>\n\n"
            "Ro'yxatdan o'tish ochiq.\n"
            "O'yinchilar: <b>{n}/{max}</b> (minimum {min})\n\n"
            "{players}"
        ),
        "reg_empty": "Hali hech kim yo'q",
        "need_admin": "⚠️ Botni admin qiling: xabarlarni o'chirish va a'zolarni cheklash.",
        "game_started": (
            "<b>O'yin boshlandi!</b>\n\n"
            "Barcha volonter o'z rollaringizni ko'rishingiz mumkin."
        ),
        "btn_view_role": "🎭 Rolni ko'rish",
        "btn_open_bot": "Botga o'tish ↗️",
        "btn_vote": "🗳 Ovoz berish",
        "night_intro": (
            "🌃 <b>Tun</b>\n"
            "Ko'chaga faqat jasur va qo'rqmas odamlar chiqishdi. Ertalab tirik qolganlarni sanaymiz..."
        ),
        "night_living": (
            "<b>Tirik o'yinchilar:</b>\n{living}\n\n"
            "Tonggacha {seconds} sek. qoldi"
        ),
        "day_intro": (
            "🏙 <b>{n}-kun</b>\n"
            "Quyosh chiqib, tunda to'kilgan qonlarni quritdi..."
        ),
        "day_living": (
            "<b>Tirik o'yinchilar:</b>\n{living}\n\n"
            "<b>Ulardan kimlar:</b>\n{roles}\n"
            "Jami: {n} kishi.\n\n"
            "Tunda bo'lgan xodisalarni muxokama qilishning ayni vaqti..."
        ),
        "vote_group": (
            "Aybdorlarni aniqlash va jazolash vaqti keldi.\n"
            "Ovoz berish uchun {seconds} sekund"
        ),
        "vote_dm": "Aybdorlarni izlash vaqti keldi!\nKimni osishni xohlaysiz?",
        "vote_dm_picked": (
            "Aybdorlarni izlash vaqti keldi!\n"
            "Kimni osishni xohlaysiz?\n\n"
            "Siz {name}ni tanladingiz"
        ),
        "flavor_manyak": "🔪 Manyak Butalar orasiga yashirinib oldi...",
        "flavor_sheriff_kill": "🕵️ Komissar Katani pistoletini o'qladi...",
        "flavor_sheriff_check": "🕵️ Komissar Katani yovuzlarni qidirishga ketdi...",
        "flavor_mashuqa": "💃 Ma'shuqa qandaydir mehmonni kutayapti...",
        "flavor_mafia": "🤵 Mafia qurbonini tanladi...",
        "flavor_doctor": "👨‍⚕️ Shifokor tungi navbatchilikga ketdi...",
        "flavor_padrajitel": "💂 Padrajitel kimnidir tanladi...",
        "flavor_journalist": "📰 Jurnalist odamlarni so'roq qilayapti...",
        "night_kill": "Tunda {role} {name} vaxshiylarcha o'ldirildi...",
        "night_kill_cause": "Aytishlaricha unikiga {killer} kelgan",
        "not_in_game": "Siz bu o'yinda emassiz.",
        "start_need_players": "O'yinni boshlash uchun kamida {min} o'yinchi kerak. Hozir: {n}.",
        "your_role": "Sizning rolingiz:\n\n{card}",
        "mafia_team": "🔫 <b>Mafia jamoasi:</b>",
        "mafia_mates_title": "🔫 Mafia azolarini eslab qoling:",
        "mafia_mate_line": "• {name} - {role} 🤵",
        "mafia_label_don": "Don",
        "mafia_label_mafiya": "Mafia",
        "mafia_vote_arrow": "🤵 {role} ({voter}) --> {target}",
        "mafia_kill_decided": "Mafialar bugun {name} ni o'ldirishga qaror qildi!",
        "mafia_change_prompt": "🔫 Kimni o'ldiramiz?",
        "btn_change_vote": "🔄 Ovozni o'zgartirish",
        "mafia_chat_hint": (
            "💬 Bot lichkasiga yozing — tirik mafia o'qiydi. "
            "Tunda kim kimga ovoz bergani jamoaga ko'rinadi."
        ),
        "mafia_chat_hint_short": "💬 Lichkaga yozing — mafia o'qiydi.",
        "mafia_pm": "{name}: {text}",
        "mafia_night_prompt": "🔫 <b>Tun.</b> Kimni o'ldiramiz?",
        "mafia_night_prompt_don": "👔 <b>Tun.</b> Kimni o'ldiramiz?",
        "mafia_vote_change_hint": "Tugmadan boshqasini bosib ovozni o'zgartirishingiz mumkin.",
        "mafia_vote_cast": "{voter} → {target} ga ovoz berdi",
        "mafia_vote_cast_skip": "{voter} ovoz bermadi",
        "mafia_votes_header": "🔫 <b>Mafia ovozlari:</b>",
        "mafia_vote_item": "• {voter} → {target}",
        "mafia_vote_pending": "• {name} — kutilyapti",
        "mafia_vote_skip_line": "• {name} — o'tkazdi",
        "mafia_vote_leader": "Yetakchi: {name} ({n})",
        "mafia_vote_tie_don": "Teng: {names}. Don tanlovi: {name}",
        "mafia_vote_tie_wait": "Teng: {names}. Don hal qiladi.",
        "mafia_vote_none": "Hali ovoz yo'q.",
        "you_mark": " ← siz",
        "boss_mark": " (Don)",
        "night_public": (
            "🌙 <b>Tun {n}</b>\n\n"
            "<b>Tirik o'yinchilar:</b>\n{living}\n\n"
            "{roles}"
        ),
        "remaining_roles_title": "O'yinda qolgan rollar:",
        "day_public": "☀️ <b>Kun {n}</b>\n\n{report}\n\n<b>Tirik o'yinchilar:</b>\n{living}\n\nMuhokama qiling. ⏳ {seconds} soniya",
        "vote_public": "Aybdorlarni aniqlash va jazolash vaqti keldi.\nOvoz berish uchun {seconds} sekund",
        "krasotka_no_vote": "\n💃 {name} bu kun ovoz bera olmaydi (Ma'shuqa).",
        "confirm_public": "Rostdan xam {name}ni osmoqchimisiz?",
        "confirm_closed": "Rostdan xam {name}ni osmoqchimisiz?\n\nOvoz berish tugadi",
        "lynch_hang_result": (
            "Ovoz berish natijalari:\n"
            "{yes} 👍  |  {no} 👎\n\n"
            "{name} - ni osamiz! :)"
        ),
        "lynch_was_role": "{name} - {role} edi",
        "lynch_no_agree": (
            "Aholi kelisha olmadi ({yes} 👍 | {no} 👎 )... "
            "Kelisha olmaslik oqibatida hech kim osilmadi..."
        ),
        "vote_cast": "{voter} - {target}ga ovoz berdi",
        "vote_cast_skip": "{voter} ovoz bermadi",
        "killers_two": "{a} va {b}",
        "night_pick": "Siz {name} ni tanladingiz.",
        "night_pick_kill": "Siz {name} ni o'ldirishni tanladingiz.",
        "night_pick_check": "Siz {name} ni tekshirishni tanladingiz.",
        "win_side_town": "Tinch aholi",
        "win_side_mafia": "Mafia",
        "win_side_manyak": "Qotil",
        "end_title": "O'yin tugadi!",
        "end_winner_side": "G'olib: {side}",
        "end_winners_title": "G'oliblar:",
        "end_others_title": "Qolgan o'yinchilar:",
        "end_duration": "O'yin: {duration} davom etdi",
        "new_don": "Yangi don - {name}",
        "new_don_dm": "🤵 Siz yangi Donsiz.",
        "stats_global": (
            "📊 <b>Bot statistikasi</b>\n\n"
            "O'yinlar: <b>{games}</b>\n"
            "O'yinchilar: <b>{players}</b>\n"
            "Mukofot: <b>{money}$</b>"
        ),
        "stats_group": (
            "📊 <b>Guruh statistikasi</b>\n\n"
            "O'yinlar: <b>{games}</b>\n"
            "Tinch aholi: <b>{town}</b>\n"
            "Mafia: <b>{mafia}</b>\n"
            "Qotil: <b>{manyak}</b>\n"
            "Mukofot: <b>{money}$</b>"
        ),
        "rating_title_global": "🏆 <b>Umumiy reyting</b>",
        "rating_title_group": "🏆 <b>Guruh reytingi</b>",
        "rating_line": "{n}. {name} — {money}$",
        "rating_you": "Sizning o'rningiz: <b>#{rank}</b> ({money}$)",
        "rating_unranked": "Siz hali reytingda emassiz.",
        "rating_empty": "Hali reyting yo'q.",
        "rank_dash": "—",
        "duration_ms": "{m} min. {s} sek.",
        "duration_hms": "{h} soat {m} min. {s} sek.",
        "vote_line": "{voter} → {target}",
        "vote_line_skip": "{voter} → o'tkazish",
        "vote_self": "O'zingizga ovoz bera olmaysiz.",
        "vote_dead": "O'lgan o'yinchilar ovoz bera olmaydi.",
        "vote_nominee": "Osilayotgan odam o'ziga ovoz bera olmaydi.",
        "vote_already": "Siz allaqachon ovoz berdingiz.",
        "vote_blocked": "Bu kun ovoz bera olmaysiz.",
        "vote_not_now": "Hozir ovoz berish emas.",
        "vote_accepted": "Ovoz qabul qilindi",
        "not_in_this_game": "Siz o'yinda emassiz.",
        "confirm_not_now": "Hozir tasdiqlash emas.",
        "confirm_accepted": "Qabul qilindi",
        "confirm_group_only": "Osishga ovoz faqat guruhda beriladi.",
        "lynch_rejected": "Osish tasdiqlanmadi.",
        "lynch_score_yes": (
            "Xisob {yes}-{no} va Xalq {name} ni osishga qaror qildi ☠️"
        ),
        "lynch_score_tie": (
            "Xisob {yes}-{no} durang Xalq bir qarorga kela olmadi. "
            "Shuning uchun hozircha yashay qoldin"
        ),
        "lynch_score_no": (
            "Xisob {yes}-{no} Xalq bir qarorga kela olmadi. "
            "Shuning uchun hozircha yashay qoldin"
        ),
        "afk_death": "{name} uxlab qolgani uchun o'lib qoldi.",
        "suicide_death": (
            "{name} bu shahardagi yovuzliklarga chiday olmasdan o'zini osib qo'ydi ☠️"
        ),
        "admin_removed": "⚖️ Admin {name} ni o'yindan chiqardi.",
        "exit_not_in_game": "Siz hozir o'yinda emassiz.",
        "exit_already_dead": "Siz allaqachon o'lgansiz.",
        "exit_not_now": "Hozir /exit qilib bo'lmaydi.",
        "sheriff_promoted": "🎖️ {name} endi sherif!",
        "sheriff_promoted_dm": "🎖️ Endi siz yangi sherifsiz.",
        "city_sleeps": "Shahar uxlaydi...",
        "vote_who": "Aybdorlarni izlash vaqti keldi!\nKimni osishni xohlaysiz?",
        "confirm_ask_dm": "⚖️ {name} ni osamizmi?",
        "death_line": "💀 {name} o'ldi — {role}",
        "night_none": "Tunda hech kim o'lmadi.",
        "night_some": "Tunda:\n{lines}",
        "lynch": "🕯 Shahar {name} ni osdi. Roli: {role}",
        "no_lynch": "Osish bo'lmadi. Shahar uxlaydi...",
        "votes_title": "Ovozlar:",
        "vote_skip": "O'tkazish",
        "no_votes": "Hech kim ovoz bermadi.",
        "win_town": "🏆 <b>Shahar g'alaba qozondi!</b> Mafiya va manyak yo'q qilindi.",
        "win_mafia": "🏆 <b>Mafiya g'alaba qozondi!</b> Shahar taslim.",
        "win_manyak": "🏆 <b>Manyak g'alaba qozondi!</b> Shaharda faqat aqldan ozgan qotil qoldi.",
        "game_over": "O'yin tugadi.",
        "reveal_title": "🃏 <b>Rollar:</b>",
        "game_stopped": "⛔ O'yin to'xtatildi.",
        "gif_admin_only": "Bu buyruq faqat admin uchun.",
        "gif_send_tun": "Tun GIFini yuboring. Bekor qilish: /cancel",
        "gif_send_tong": "Tong GIFini yuboring. Bekor qilish: /cancel",
        "gif_saved_tun": "✅ Tun GIFi saqlandi. Endi har tun shu GIF ketadi.",
        "gif_saved_tong": "✅ Tong GIFi saqlandi. Endi har kun boshida shu GIF ketadi.",
        "gif_need_gif": "GIF yuboring (rasm emas). Bekor: /cancel",
        "gif_cancelled": "GIF o'zgartirish bekor qilindi.",
        "no_reg": "Hozir ro'yxatdan o'tish yo'q.",
        "only_host_admin": 'Faqat boshlovchi yoki admin.',
        "reg_extended": "⏳ Ro'yxat {seconds} soniyaga uzaytirildi.",
        "no_game_now": "O'yin yo'q.",
        "cannot_leave_now": "Hozir chiqib bo'lmaydi.",
        "not_on_list": "Siz ro'yxatda yo'qsiz.",
        "host_cannot_leave": "Boshlovchi chiqa olmaydi. O'yinni /stop qiling.",
        "left_ok": 'Chiqdingiz.',
        "cannot_start_now": "O'yinni hozir boshlab bo'lmaydi.",
        "only_host_start": 'Faqat boshlovchi start bosa oladi.',
        "need_n_players": "Kamida {n} o'yinchi kerak.",
        "starting": "O'yin boshlanmoqda...",
        "game_cancelled_min": "O'yin bekor qilindi — kamida {n} o'yinchi kerak.",
        "dm_role_failed": "⚠️ {name} bot lichkasini ochmagan — rol yetib bormagan bo'lishi mumkin.",
        "bad_button": "Noto'g'ri tugma.",
        "not_night": 'Hozir tun emas.',
        "cannot_act": 'Siz yurish qila olmaysiz.',
        "not_sheriff": 'Siz sherif emassiz.',
        "skipped": "O'tkazildi",
        "move_skipped": "⏭ Yurish o'tkazildi.",
        "bad_choice": "Noto'g'ri tanlov.",
        "sheriff_check_who": 'Kimni tekshirasiz?',
        "sheriff_kill_who": "Kimni o'ldirasiz?",
        "bad_target": "Noto'g'ri nishon.",
        "not_journalist": 'Siz jurnalist emassiz.',
        "pick_two_people": 'Ikkita turli odam tanlang.',
        "not_your_move": 'Bu sizning yurishingiz emas.',
        "already_acted": 'Siz allaqachon yurdingiz.',
        "cannot_self": "O'zingizni tanlab bo'lmaydi.",
        "doctor_no_repeat": "Ketma-ket ikki tun bir odamni davolab bo'lmaydi.",
        "night_prompt_sheriff": "🕵️ <b>Tun.</b> Tekshirasizmi yoki o'ldirasizmi?",
        "night_prompt_krasotka": '💄 <b>Tun.</b> Kimni band qilasiz? Tanlangan odam ertasi kuni ovoz bera olmaydi.',
        "night_prompt_doktor": '🩺 <b>Tun.</b> Kimni davolaysiz?',
        "night_prompt_doktor_last": "\n⚠️ Ketma-ket {name} ni davolab bo'lmaydi.",
        "night_prompt_potrashitel": "🔪 <b>Tun.</b> Kimni otasiz? (faqat rol egalari o'ladi)",
        "night_prompt_manyak": "🧠 <b>Tun.</b> Kimni o'ldirasiz?",
        "night_prompt_jurnalist": '📰 <b>Tun.</b> Birinchi odamni tanlang.',
        "pick_second": 'Ikkinchi odamni tanlang:',
        "sheriff_check_blocked": "🔍 Bu tunda tekshirib bo'lmadi (Ma'shuqa himoyasi).",
        "sheriff_check_mafia": '🔍 {name} — <b>Mafiya</b>.',
        "sheriff_check_not": '🔍 {name} — <b>Mafiya emas</b>.',
        "sergeant_watch": '🎖️ Sherif {name} ni tekshirdi.{extra}',
        "sergeant_mafia": ' (natija: Mafiya)',
        "sergeant_not_mafia": ' (natija: Mafiya emas)',
        "sergeant_blocked": " (himoya tufayli natija yo'q)",
        "sheriff_you_now": "🎖️ Sherif o'ldi. Endi <b>siz yangi sherifsiz</b>.",
        "sergeant_now_sheriff": "🎖️ Serjant yangi sherif bo'ldi.",
        "journalist_blocked": "Bu tunda ma'lumot olinmadi (Ma'shuqa himoyasi).",
        "journalist_same": '📰 {a} va {b}: <b>Rollar bir xil</b>.',
        "journalist_diff": '📰 {a} va {b}: <b>Rollar xar xil</b>.',
        "potrashitel_immune": "🔪 O'q tekmadi. Bu odamning o'qqa sezgir roli yo'q.",
        "yakudza_prompt": "🥋 Siz o'ldingiz, lekin oxirgi zarbani qilasiz. Kimni o'ldirasiz? (100%)",
        "yakudza_dm_fail": "Yakudza lichkaga yozolmadi — qasos bo'lmadi.",
        "game_not_found": "O'yin topilmadi.",
        "not_revenge_time": 'Hozir qasos vaqti emas.',
        "revenge_skipped": "Qasos o'tkazildi",
        "revenge_skipped_long": "Qasos o'tkazildi.",
        "revenge_ok": 'Qasos qabul qilindi',
        "revenge_ok_long": '✅ Qasos qabul qilindi.',
        "yakudza_kill": "🥋 Yakudza qasosi: {name} o'ldi — {role}.",
        "bad_role": "Noto'g'ri rol.",
        "bot_started": 'Bot ishga tushdi',
        "too_many_requests": "Juda ko'p so'rov. Biroz kuting.",
        "cmd_start": 'Bot haqida',
        "cmd_help": 'Yordam',
        "cmd_rules": 'Rollar qoidasi',
        "cmd_game": "O'yinni boshlash",
        "cmd_extend": "Ro'yxatni uzaytirish",
        "cmd_stop": "O'yinni to'xtatish",
        "cmd_settings": 'Guruh sozlamalari',
        "cmd_stats": 'Statistika',
        "cmd_rating": 'Reyting',
        "cmd_addadmin": "Shtabga qo'shish",
        "cmd_deladmin": 'Shtabdan olish',
        "cmd_gif_night": "Tun GIFini o'zgartirish",
        "cmd_gif_day": "Tong GIFini o'zgartirish",
        "cmd_cancel": "GIF o'zgartirishni bekor qilish",
        "test_someone": "kimdir",
        "test_talk_wrap": "💬 <b>{name}</b>: {text}",
        "test_talk": (
            "{name} o'zini qanday tutayotgani yoqmayapti.\n"
            "Shoshilmaylik. Tun g'alati o'tdi.\n"
            "Men tinchman, yashiradigan narsam yo'q.\n"
            "Komissar, agar tirik bo'lsang — ishora ber.\n"
            "{name} juda jim. Shubhali.\n"
            "{name} ni osamizmi? Yoki erta?\n"
            "Doktor, uxlamagin, biz oz qoldik.\n"
            "Mafia hozir aniq bittasiga bosim qilyapti.\n"
            "Birinchi duch kelganni ovozga qo'ymagan bo'lardim.\n"
            "Kimdir ko'zida yolg'onni ko'rdimi?\n"
            "{name}, oqlan. Nega jimsin?\n"
            "Komissar otgan bo'lsa — kimga otganini ayt.\n"
            "Menga {name} juda ishonchli o'ynayotgandek.\n"
            "Shahar, o'zlaringizni osmang. O'ylab ko'ring.\n"
            "{name} haqida yomon hisobim bor.\n"
            "Avval hammani eshitaylik.\n"
            "Tunda kimdir aniq noto'g'ri nishonga olgan.\n"
            "Men bosh bilan ovoz beraman, hissiyot bilan emas.\n"
            "{name} kecha ham g'alati tutdi.\n"
            "Agar bu mafia bo'lsa — hozir bizni to'qnashtirishadi."
        ),
        "btn_skip": "⏭ O'tkazish",
        "btn_check": "🔍 Tekshirish",
        "btn_kill": "🔫 O'ldirish",
        "btn_yes": "✅ Ha, osilsin",
        "btn_no": "❌ Yo'q",
        "role_aholi": "👨🏼 Tinch aholi",
        "role_krosniy_otets": "🤵 Don",
        "role_mafiya": "🤵 Mafia",
        "role_sherif": "🕵️ Komissar Katani",
        "role_serjant": "💂 Serjant",
        "role_doktor": "👨‍⚕️ Shifokor",
        "role_manyak": "🔪 Qotil",
        "role_krasotka": "💃 Ma'shuqa",
        "role_potrashitel": "💂 Padrajitel",
        "role_jurnalist": "📰 Jurnalist",
        "role_yakudza": "🤞 Yakudza",
        "alert_aholi": "Siz- 👨🏼 Tinch aholisiz!\nMaxsus kuch yo'q. Kunduzi ovoz berib shaharni himoya qilasiz.",
        "alert_krosniy_otets": "Siz- 🤵 Donsiz!\nMafia boshlig'isiz. Tunda ko'p ovoz olgan o'ladi; teng bo'lsa siz hal qilasiz.",
        "alert_mafiya": "Siz- 🤵 Mafiasiz!\nTunda jamoa bilan 1 kishini o'ldirasiz. Ovozlar jamoaga ko'rinadi, tenglikda Don hal qiladi.",
        "alert_sherif": "Siz- 🕵️ Komissar Katanisiz!\nTunda tekshirasiz yoki o'ldirasiz. Tekshiruv: Mafiya / Mafiya emas.",
        "alert_serjant": "Siz- 💂 Serjantsiz!\nKomissar yurishlarini ko'rasiz. Komissar o'lsa — yangi komissar bo'lasiz.",
        "alert_doktor": "Siz- 👨‍⚕️ Shifokorsiz!\nTunda 1 kishini davolaysiz. Ketma-ket bir odamni davolab bo'lmaydi. Qotil/Padrajiteldan qutqara olmaysiz.",
        "alert_manyak": "Siz- 🔪 Qotilsiz!\nHar tunda 1 kishini o'ldirasiz. Shifokor siznikini qutqara olmaydi. Yakka g'alaba qilasiz.",
        "alert_krasotka": "Siz- 💃 Ma'shuqasiz!\nTunda 1 kishini band qilasiz: unga tegolmaydi, u ovoz bera olmaydi. Donni tanlasangiz mafiya o'ldirmaydi.",
        "alert_potrashitel": "Siz- 💂 Padrajitelsiz!\nYaxshilar tomonidasiz. Faqat rol egalarini ota olasiz. Tinch aholi va Yakudza o'lmaydi.",
        "alert_jurnalist": "Siz- 📰 Jurnalistsiz!\nTunda 2 kishini solishtirasiz: ikkalasi ham mafiya yoki yo'q — bir xil / xar xil.",
        "alert_yakudza": "Siz- 🤞 Yakudzasiz!\nAholiga o'xshaysiz. Osishsa yoki tunda o'ldirishsa, 1 kishini 100% o'ldirasiz.",
        "card_aholi": "👨🏼 <b>Tinch aholi</b>\nMaxsus qobiliyat yo'q. Kunduzgi ovozda shahar uchun o'ynaysiz.",
        "card_krosniy_otets": "🤵 <b>Don</b>\nMafia boshlig'i. Tunda ko'p ovoz olgan o'ladi; teng yoki chalkash ovozlarni siz hal qilasiz. Ma'shuqa sizni tanlasa, mafiya o'ldira olmaydi.",
        "card_mafiya": "🤵 <b>Mafia</b>\nTunda jamoa bilan 1 kishini o'ldirasiz. Ovozlar lichkada ko'rinadi. Tenglikda Don hal qiladi.",
        "card_sherif": "🕵️ <b>Komissar Katani</b>\nTunda tekshirish yoki o'ldirish. Javob: Mafiya / Mafiya emas. Qotil — mafiya emas.",
        "card_serjant": "💂 <b>Serjant</b>\nKomissar kimni tekshirgani/o'ldirishga uringanini ko'rasiz. Komissar o'lsa yangi komissar bo'lasiz.",
        "card_doktor": "👨‍⚕️ <b>Shifokor</b>\nTunda o'zingiz yoki 1 odamni davolaysiz. Ketma-ket bir xil odamni davolab bo'lmaydi. Qotil va rolga ega Padrajitel o'qidan qutqara olmaysiz.",
        "card_manyak": "🔪 <b>Qotil</b>\nYakka qotil. Har tunda 1 kishi. Shifokor qutqara olmaydi.",
        "card_krasotka": "💃 <b>Ma'shuqa</b>\nTunda 1 odamni band qilasiz. Unga (Padrajitel/Komissar o'ldirishidan tashqari) tegolmaydi. U ertasi kuni ovoz bera olmaydi. Donni tanlasangiz mafiya o'ldirmaydi. Sizni tunda faqat Komissar yoki Padrajitel o'ldira oladi.",
        "card_potrashitel": "💂 <b>Padrajitel</b>\nYaxshilar tomoni. Faqat rol egalarini o'ldiradi. Yakudza va tinch aholi o'lmaydi.",
        "card_jurnalist": "📰 <b>Jurnalist</b>\nTunda 2 odam: 1 mafiya + 1 boshqa → xar xil; ikkalasi mafiya yoki ikkalasi emas → bir xil.",
        "card_yakudza": "🤞 <b>Yakudza</b>\nYaxshilar tomoni, aholiga o'xshaydi. O'lganda 1 kishini 100% o'ldiradi.",
    },
    "ru": {
        "start": "Привет!\nЯ 🤵🏻 официальный бот игры Мафия.",
        "btn_add_group": "🤵🏻 Добавить бота в группу ↗️",
        "btn_join_group": "🎲 Войти в группу",
        "btn_language": "🇷🇺 Язык / Language",
        "btn_profile": "👤 Профиль",
        "btn_roles": "🎭 Роли",
        "btn_stats": "📊 Статистика",
        "btn_rating": "🏆 Рейтинг",
        "btn_close": "❌ Закрыть",
        "btn_shop": "🛒 Магазин",
        "btn_market": "🎁 Маркет",
        "btn_profile_app": "👤 Профиль",
        "btn_topup": "💳 Пополнить",
        "btn_buy_money": "Купить 💵",
        "btn_buy_gems": "Купить 🪙",
        "btn_buy_vcoin": "Купить 🪙",
        "btn_use": "✅ Использовать",
        "btn_armed": "⏳ Следующая игра",
        "btn_pick_role": "🎭 Выбрать роль",
        "btn_stars": "⭐ Vcoin",
        "shop_soon": "Магазин скоро.",
        "shop_title": "<b>Магазин</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_header": "<b>Магазин</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_item_line": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_item_card": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_price_money": "💵 {n}",
        "shop_price_vcoin": "🪙 {n}",
        "shop_empty": "Товаров пока нет.",
        "shop_bought": "Куплено: {item}",
        "shop_broke": "Недостаточно средств.",
        "shop_missing": "Товар не найден.",
        "shop_off": "Товар выключен.",
        "shop_no_price": "У товара нет цены.",
        "shop_used": "Сработает в следующей игре: {item}",
        "shop_already": "Уже поставлено на следующую игру.",
        "shop_need_item": "Сначала купите.",
        "shop_need_pick": "Сначала выберите роль.",
        "shop_role_saved": "Выбранная роль: {role}",
        "shop_pick_title": "Какую роль хотите получить?",
        "shop_armed_line": "Следующая игра: {items}",
        "shop_pick_now": "Выбрано: {role}",
        "role_active_public": "🎎 Активная роль",
        "protect_fired": "Чья-то защита сработала!",
        "stars_title": "<b>Пакеты Vcoin</b>\nЗа Telegram Stars.",
        "stars_invoice": "{n} Vcoin",
        "stars_desc": "VolMafia Vcoin",
        "stars_ok": "+{n} Vcoin зачислено.",
        "stars_off": "Оплата Stars сейчас недоступна.",
        "gift_ok": "Заказ принят. Админ свяжется с вами.",
        "gift_broke": "Недостаточно Vcoin.",
        "gift_missing": "Подарок не найден.",
        "gift_busy": "Дождитесь выполнения предыдущих заказов.",
        "shop_boost_fail_chosen": "Выбранная роль в этой игре не встала. Заряд сохранён.",
        "shop_boost_fail_active": "Активная роль в этой игре не выдана. Заряд сохранён.",
        "gift_done_dm": "🎁 Заказ выполнен: {title}",
        "gift_cancel_dm": "🎁 Заказ отменён. 🪙 {n} Vcoin возвращено.",
        "gift_admin": "🎁 Новый заказ #{id}\n{name} (<code>{uid}</code>) {user}\n{emoji} {title}\n🪙 {vcoin}",
        "market_need_https": "Для Mini App Market нужен HTTPS в PANEL_PUBLIC_URL.",
        "market_tab_gifts": "🎁 Подарки",
        "market_tab_boosts": "🎎 Игра",
        "market_tab_stars": "⭐ Vcoin",
        "market_tab_swap": "💵 $",
        "market_empty_gifts": "Сейчас нет открытых подарков.",
        "market_empty_shop": "Нет товаров.",
        "market_empty_packs": "Нет пакетов.",
        "market_empty_swap": "Нет обмена.",
        "market_confirm_gift": "Списать {n} Vcoin за {title}? Админ выдаст вручную.",
        "market_confirm_swap": "Обменять {v} Vcoin на {m}$?",
        "market_swap_ok": "+{m}$ · −{v} Vcoin",
        "market_swap": "Обменять",
        "market_swap_hint": "Обмен Vcoin на обычные $. Пополнение — отдельно.",
        "market_auth": "Откройте Market через Telegram Mini App.",
        "market_error": "Ошибка. Попробуйте ещё раз.",
        "market_bought": "Куплено.",
        "market_used": "Поставлено на следующую игру.",
        "market_add": "Добавить",
        "market_buy": "Купить",
        "market_close": "Закрыть",
        "app_profile": "Профиль",
        "app_topup": "Пополнение",
        "topup_pick": "Выберите способ оплаты",
        "topup_kind": "Что пополнить?",
        "pay_stars": "⭐ Telegram Stars",
        "pay_stars_desc": "Купите Vcoin за Telegram Stars.",
        "pay_market": "🎁 Маркет",
        "pay_market_desc": "Баланс можно пополнить и через Маркет.",
        "pay_vcoin": "🪙 Vcoin",
        "pay_vcoin_desc": "Купите Vcoin за Telegram Stars.",
        "pay_money": "💵 Деньги ($)",
        "pay_money_desc": "Купите $ за Telegram Stars.",
        "profile_games": "Игры",
        "profile_wins": "Победы",
        "profile_inv": "Инвентарь",
        "profile_empty_inv": "Инвентарь пуст.",
        "profile_badges": "Badge",
        "profile_badges_empty": "Пока нет Badge.",
        "topup_hint": "Сначала способ, затем пакет.",
        "topup_hint_kind": "Сначала Vcoin или $, затем пакет.",
        "stars_ok_money": "+{n}$ зачислено.",
        "stars_invoice_money": "{n}$",
        "stars_desc_money": "VolMafia $",
        "maintenance": "Бот на техпаузе. Попробуйте позже.",
        "user_banned": "Вам нельзя играть.",
        "group_banned": "В этой группе играть нельзя.",
        "join_banned": "Вы заблокированы.",
        "staff_not_super": "Только супер-админ.",
        "staff_wait": "Пришлите ID или перешлите сообщение.",
        "staff_need_user": "Нужен ID или reply.",
        "staff_pick": "Роль для {name} (<code>{id}</code>):",
        "staff_added": "В штаб: <code>{id}</code> — {role}",
        "staff_removed": "Убран из штаба: <code>{id}</code>",
        "staff_env": "ENV-админа нельзя снять.",
        "staff_cancelled": "Отменено.",
        "staff_only": "Этот раздел только для админов.",
        "staff_role_super": "👑 Super",
        "staff_role_moderator": "🛡️ Модератор",
        "staff_role_ads": "📣 Ads",
        "btn_back": "🔙 Назад",
        "roles_title": "<b>Список доступных ролей</b>\nНажмите на роль, чтобы увидеть описание",
        "lang_title": "Выберите язык / Choose language:",
        "lang_pick_first": (
            "🌐 Tilni tanlang\n"
            "Выберите язык\n"
            "Choose language"
        ),
        "lang_uz": "🇺🇿 O'zbekcha",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "lang_saved": "Язык изменён: Русский",
        "profile_text": (
            "👤 {username}\n"
            "💵 Деньги: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Защита: {protection}\n"
            "📁 Документы: {documents}\n"
            "🎎 Активная роль: {active_role}\n"
            "🎭 Выбранная роль: {chosen_role}"
        ),
        "profile_body": (
            "👤 {username}\n"
            "💵 Деньги: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Защита: {protection}\n"
            "📁 Документы: {documents}\n"
            "🎎 Активная роль: {active_role}\n"
            "🎭 Выбранная роль: {chosen_role}"
        ),
        "profile_win_header": (
            "<b>Игра окончена</b>\n"
            "За победу в роли \"{role}\" вам начислено 💵 {amount}!"
        ),
        "profile_reward_header": (
            "<b>Игра окончена</b>\n"
            "За роль \"{role}\" вам начислено 💵 {amount}!"
        ),
        "group_settings": (
            "⚙️ <b>Настройки группы</b>\n\n"
            "🌐 Язык: {lang_name}\n"
            "▶️ Auto-start: {auto}"
        ),
        "group_lang_admin": "Язык может менять только админ группы.",
        "group_settings_admin": "Настройки может менять только админ группы.",
        "auto_on": "включён",
        "auto_off": "выключен",
        "auto_enabled": "Auto-start включён.",
        "auto_disabled": "Auto-start выключен.",
        "btn_auto_on": "✅ Auto-start: включён",
        "btn_auto_off": "❌ Auto-start: выключен",
        "reg_wait_start": "⏳ Набор закончился. Auto-start выключен — начните игру командой /start.",
        "no_group_link": "Ссылка на игровую группу ещё не задана.",
        "help_private": (
            "🎭 Я веду <b>Мафию</b> в группе.\n\n"
            "1) Добавьте бота в группу и дайте <b>админа</b>.\n"
            "2) Напишите /game в группе.\n"
            "3) Сначала нажмите /start здесь, потом присоединяйтесь.\n"
            "4) 🛒 Магазин — защита/документы ($), активная/выбранная роль (Vcoin).\n"
            "5) 🎁 Маркет — реальные подарки за Vcoin."
        ),
        "help_group": (
            "🎭 <b>Команды</b>\n"
            "/game — открыть набор\n"
            "/start — начать игру\n"
            "/extend — продлить набор\n"
            "/stop — остановить игру\n"
            "/exit — покончить с собой\n"
            "/game-test N — тест (боты, только админ)\n"
            "/settings — настройки группы\n"
            "/qoidalar — роли"
        ),
        "btn_join": "✅ Присоединиться",
        "join_ok": "Вы успешно присоединились к игре {group}",
        "join_already": "Потерпите, вы уже в игре! Понимаете? В игре! :)",
        "join_closed": "Набор сейчас закрыт.",
        "join_full": "Мест больше нет.",
        "join_other": "Вы уже в другой игре.",
        "join_not_found": "Игра не найдена. Напишите /game в группе.",
        "btn_leave": "❌ Выйти",
        "btn_start_game": "▶️ Начать игру",
        "btn_group_lang": "🌐 Язык",
        "reg_already": "Набор уже идёт.",
        "game_already": "В этой группе игра уже идёт.",
        "test_usage": (
            "🧪 Тест: <code>/game-test 8</code>\n"
            "Набор как в обычной игре. N — всего игроков (люди + боты), {min}–{max}."
        ),
        "test_admin_only": "Тестовый режим может включить только админ группы или админ бота.",
        "test_pick_role": (
            "🧪 <b>Тестовый режим</b>\n"
            "Игроки: <b>{n}</b> (вы + {bots} ботов)\n\n"
            "Выберите себе роль. Остальные роли боты получат случайно.\n"
            "Боты играют на русском. Статистика не пишется."
        ),
        "test_pick_role_dm": (
            "🧪 <b>Тест.</b> Выберите себе роль.\n"
            "Выбор виден только вам. Можно сменить до старта.\n"
            "Если не выберете — роль выдадут случайно."
        ),
        "test_role_picked": (
            "🧪 Вы выбрали {role}.\n"
            "До старта можно сменить роль другой кнопкой."
        ),
        "test_role_taken": "Эта роль занята. Выберите другую.",
        "test_started": (
            "🧪 <b>Тест начался.</b> Люди: {humans}, боты: {bots}.\n"
            "Боты будут писать в группе по-русски и ходить ночью/на голосовании сами. Статистика не пишется."
        ),
        "test_setup_timeout": "🧪 Тест отменён — роль не выбрана.",
        "test_not_setup": "Сейчас нельзя выбрать тестовую роль.",
        "test_only_host": "Роль выбирает только тот, кто запустил тест.",
        "test_pick_pending": "Сначала выберите роль для теста или нажмите /stop.",
        "test_reg_text": (
            "🧪 <b>Тест Мафия</b>\n\n"
            "Набор открыт (как в обычной игре).\n"
            "Люди: <b>{n}/{max}</b>\n"
            "Ботов при старте: <b>{bots}</b>\n\n"
            "Роль выберите в личке бота — это лично.\n\n"
            "{players}"
        ),
        "reg_text": (
            "🎭 <b>Игра Мафия</b>\n\n"
            "Набор открыт.\n"
            "Игроки: <b>{n}/{max}</b> (минимум {min})\n\n"
            "{players}"
        ),
        "reg_empty": "Пока никого нет",
        "need_admin": "⚠️ Сделайте бота админом: удаление сообщений и ограничение участников.",
        "game_started": (
            "<b>Игра началась!</b>\n\n"
            "Все волонтёры могут посмотреть свои роли."
        ),
        "btn_view_role": "🎭 Посмотреть роль",
        "btn_open_bot": "Перейти в бота ↗️",
        "btn_vote": "🗳 Голосовать",
        "night_intro": (
            "🌃 <b>Ночь</b>\n"
            "На улицу вышли только смелые. Утром посчитаем живых..."
        ),
        "night_living": (
            "<b>Живые игроки:</b>\n{living}\n\n"
            "До утра {seconds} сек."
        ),
        "day_intro": (
            "🏙 <b>{n}-й день</b>\n"
            "Солнце взошло и высушило ночную кровь..."
        ),
        "day_living": (
            "<b>Живые игроки:</b>\n{living}\n\n"
            "<b>Среди них:</b>\n{roles}\n"
            "Всего: {n} чел.\n\n"
            "Самое время обсудить события ночи..."
        ),
        "vote_group": (
            "Пора искать виновных и наказывать.\n"
            "На голосование {seconds} секунд"
        ),
        "vote_dm": "Пора искать виновных!\nКого хотите повесить?",
        "vote_dm_picked": (
            "Пора искать виновных!\n"
            "Кого хотите повесить?\n\n"
            "Вы выбрали: {name}"
        ),
        "flavor_manyak": "🔪 Маньяк спрятался в кустах...",
        "flavor_sheriff_kill": "🕵️ Комиссар Катани зарядил пистолет...",
        "flavor_sheriff_check": "🕵️ Комиссар Катани ушёл искать злодеев...",
        "flavor_mashuqa": "💃 Красотка ждёт гостя...",
        "flavor_mafia": "🤵 Мафия выбрала жертву...",
        "flavor_doctor": "👨‍⚕️ Доктор вышел на ночное дежурство...",
        "flavor_padrajitel": "💂 Потрашитель кого-то выбрал...",
        "flavor_journalist": "📰 Журналист допрашивает людей...",
        "night_kill": "Ночью {role} {name} был(а) жестоко убит(а)...",
        "night_kill_cause": "Говорят, к нему приходил {killer}",
        "not_in_game": "Вы не в этой игре.",
        "start_need_players": "Чтобы начать, нужно минимум {min} игроков. Сейчас: {n}.",
        "your_role": "Ваша роль:\n\n{card}",
        "mafia_team": "🔫 <b>Команда мафии:</b>",
        "mafia_mates_title": "🔫 Запомните членов мафии:",
        "mafia_mate_line": "• {name} - {role} 🤵",
        "mafia_label_don": "Дон",
        "mafia_label_mafiya": "Мафия",
        "mafia_vote_arrow": "🤵 {role} ({voter}) --> {target}",
        "mafia_kill_decided": "Мафия решила сегодня убить {name}!",
        "mafia_change_prompt": "🔫 Кого убиваем?",
        "btn_change_vote": "🔄 Сменить голос",
        "mafia_chat_hint": (
            "💬 Пишите боту в личку — живая мафия увидит. "
            "Ночью видно, кто за кого голосует."
        ),
        "mafia_chat_hint_short": "💬 Пишите в личку — мафия читает.",
        "mafia_pm": "{name}: {text}",
        "mafia_night_prompt": "🔫 <b>Ночь.</b> Кого убиваем?",
        "mafia_night_prompt_don": "👔 <b>Ночь.</b> Кого убиваем?",
        "mafia_vote_change_hint": "Можно сменить голос другой кнопкой.",
        "mafia_vote_cast": "{voter} → голос за {target}",
        "mafia_vote_cast_skip": "{voter} не стал(а) голосовать",
        "mafia_votes_header": "🔫 <b>Голоса мафии:</b>",
        "mafia_vote_item": "• {voter} → {target}",
        "mafia_vote_pending": "• {name} — ждём",
        "mafia_vote_skip_line": "• {name} — пропуск",
        "mafia_vote_leader": "Лидер: {name} ({n})",
        "mafia_vote_tie_don": "Ничья: {names}. Выбор Дона: {name}",
        "mafia_vote_tie_wait": "Ничья: {names}. Решает Дон.",
        "mafia_vote_none": "Пока нет голосов.",
        "you_mark": " ← вы",
        "boss_mark": " (Крёстный отец)",
        "night_public": (
            "🌙 <b>Ночь {n}</b>\n\n"
            "<b>Живые игроки:</b>\n{living}\n\n"
            "{roles}"
        ),
        "remaining_roles_title": "Оставшиеся роли:",
        "day_public": "☀️ <b>День {n}</b>\n\n{report}\n\n<b>Живые игроки:</b>\n{living}\n\nОбсуждайте. ⏳ {seconds} сек.",
        "vote_public": "🗳 <b>Голосование</b>\nКого повесить?{blocked}\n\n{living}\n\n⏳ {seconds} сек.",
        "krasotka_no_vote": "\n💄 {name} сегодня не голосует (красотка).",
        "confirm_public": "Вы правда хотите повесить {name}?",
        "confirm_closed": "Вы правда хотите повесить {name}?\n\nГолосование окончено",
        "lynch_hang_result": (
            "Результаты голосования:\n"
            "{yes} 👍  |  {no} 👎\n\n"
            "{name} - вешаем! :)"
        ),
        "lynch_was_role": "{name} - {role}",
        "lynch_no_agree": (
            "Жители не смогли договориться ({yes} 👍 | {no} 👎 )... "
            "Из-за разногласий никого не повесили..."
        ),
        "vote_cast": "{voter} — {target}",
        "vote_cast_skip": "{voter} не стал(а) голосовать",
        "killers_two": "{a} и {b}",
        "night_pick": "Вы выбрали {name}.",
        "night_pick_kill": "Вы выбрали убить {name}.",
        "night_pick_check": "Вы выбрали проверить {name}.",
        "win_side_town": "Мирные",
        "win_side_mafia": "Мафия",
        "win_side_manyak": "Маньяк",
        "end_title": "Игра окончена!",
        "end_winner_side": "Победитель: {side}",
        "end_winners_title": "Победители:",
        "end_others_title": "Остальные игроки:",
        "end_duration": "Игра длилась: {duration}",
        "new_don": "Новый дон - {name}",
        "new_don_dm": "🤵 Вы новый Дон.",
        "stats_global": (
            "📊 <b>Статистика бота</b>\n\n"
            "Игр: <b>{games}</b>\n"
            "Игроков: <b>{players}</b>\n"
            "Награда: <b>{money}$</b>"
        ),
        "stats_group": (
            "📊 <b>Статистика группы</b>\n\n"
            "Игр: <b>{games}</b>\n"
            "Мирные: <b>{town}</b>\n"
            "Мафия: <b>{mafia}</b>\n"
            "Маньяк: <b>{manyak}</b>\n"
            "Награда: <b>{money}$</b>"
        ),
        "rating_title_global": "🏆 <b>Общий рейтинг</b>",
        "rating_title_group": "🏆 <b>Рейтинг группы</b>",
        "rating_line": "{n}. {name} — {money}$",
        "rating_you": "Ваше место: <b>#{rank}</b> ({money}$)",
        "rating_unranked": "Вас ещё нет в рейтинге.",
        "rating_empty": "Рейтинг пока пуст.",
        "rank_dash": "—",
        "duration_ms": "{m} мин. {s} сек.",
        "duration_hms": "{h} ч. {m} мин. {s} сек.",
        "vote_line": "{voter} → {target}",
        "vote_line_skip": "{voter} → пропуск",
        "vote_self": "Нельзя голосовать за себя.",
        "vote_dead": "Мёртвые не голосуют.",
        "vote_nominee": "Кандидат не голосует за свою казнь.",
        "vote_already": "Вы уже проголосовали.",
        "vote_blocked": "Сегодня вы не голосуете.",
        "vote_not_now": "Сейчас не время голосовать.",
        "vote_accepted": "Голос принят",
        "not_in_this_game": "Вы не в игре.",
        "confirm_not_now": "Сейчас не подтверждение.",
        "confirm_accepted": "Принято",
        "confirm_group_only": "Голос за казнь принимается только в группе.",
        "lynch_rejected": "Казнь не подтверждена.",
        "lynch_score_yes": "Счёт {yes}-{no} и народ решил повесить {name} ☠️",
        "lynch_score_tie": (
            "Счёт {yes}-{no} ничья. Народ не смог принять решение. "
            "Поэтому пока живи"
        ),
        "lynch_score_no": (
            "Счёт {yes}-{no}. Народ не смог принять решение. "
            "Поэтому пока живи"
        ),
        "afk_death": "{name} заснул(а) и умер(ла).",
        "suicide_death": (
            "{name} не выдержал(а) зла этого города и повесился(лась) ☠️"
        ),
        "admin_removed": "⚖️ Админ исключил(а) {name} из игры.",
        "exit_not_in_game": "Вы сейчас не в игре.",
        "exit_already_dead": "Вы уже мертвы.",
        "exit_not_now": "Сейчас /exit недоступен.",
        "sheriff_promoted": "🎖️ {name} теперь шериф!",
        "sheriff_promoted_dm": "🎖️ Теперь вы новый шериф.",
        "city_sleeps": "Город засыпает...",
        "vote_who": "🗳 Кого повесить?",
        "confirm_ask_dm": "⚖️ Вешаем {name}?",
        "death_line": "💀 {name} погиб — {role}",
        "night_none": "Ночью никто не погиб.",
        "night_some": "Ночью:\n{lines}",
        "lynch": "🕯 Город повесил {name}. Роль: {role}",
        "no_lynch": "Казни не было. Город засыпает...",
        "votes_title": "Голоса:",
        "vote_skip": "Пропуск",
        "no_votes": "Никто не проголосовал.",
        "win_town": "🏆 <b>Победил город!</b> Мафия и маньяк уничтожены.",
        "win_mafia": "🏆 <b>Победила мафия!</b> Город сдался.",
        "win_manyak": "🏆 <b>Победил маньяк!</b> В городе остался только безумец.",
        "game_over": "Игра окончена.",
        "reveal_title": "🃏 <b>Роли:</b>",
        "game_stopped": "⛔ Игра остановлена.",
        "gif_admin_only": "Эта команда только для админа.",
        "gif_send_tun": "Отправьте GIF ночи. Отмена: /cancel",
        "gif_send_tong": "Отправьте GIF утра. Отмена: /cancel",
        "gif_saved_tun": "✅ GIF ночи сохранён. Теперь каждую ночь будет этот GIF.",
        "gif_saved_tong": "✅ GIF утра сохранён. Теперь в начале каждого дня будет этот GIF.",
        "gif_need_gif": "Пришлите GIF (не фото). Отмена: /cancel",
        "gif_cancelled": "Смена GIF отменена.",
        "no_reg": 'Сейчас набор закрыт.',
        "only_host_admin": 'Только ведущий или админ.',
        "reg_extended": '⏳ Набор продлён на {seconds} сек.',
        "no_game_now": 'Игры нет.',
        "cannot_leave_now": 'Сейчас выйти нельзя.',
        "not_on_list": 'Вас нет в списке.',
        "host_cannot_leave": 'Ведущий не может выйти. Остановите игру /stop.',
        "left_ok": 'Вы вышли.',
        "cannot_start_now": 'Сейчас игру начать нельзя.',
        "only_host_start": 'Только ведущий может нажать start.',
        "need_n_players": 'Нужно минимум {n} игроков.',
        "starting": 'Игра начинается...',
        "game_cancelled_min": 'Игра отменена — нужно минимум {n} игроков.',
        "dm_role_failed": '⚠️ {name} не открыл(а) личку бота — роль могла не дойти.',
        "bad_button": 'Неверная кнопка.',
        "not_night": 'Сейчас не ночь.',
        "cannot_act": 'Вы не можете ходить.',
        "not_sheriff": 'Вы не шериф.',
        "skipped": 'Пропущено',
        "move_skipped": '⏭ Ход пропущен.',
        "bad_choice": 'Неверный выбор.',
        "sheriff_check_who": 'Кого проверить?',
        "sheriff_kill_who": 'Кого убить?',
        "bad_target": 'Неверная цель.',
        "not_journalist": 'Вы не журналист.',
        "pick_two_people": 'Выберите двух разных людей.',
        "not_your_move": 'Это не ваш ход.',
        "already_acted": 'Вы уже ходили.',
        "cannot_self": 'Нельзя выбрать себя.',
        "doctor_no_repeat": 'Нельзя лечить одного человека две ночи подряд.',
        "night_prompt_sheriff": '🕵️ <b>Ночь.</b> Проверить или убить?',
        "night_prompt_krasotka": '💄 <b>Ночь.</b> Кого заблокировать? Завтра этот игрок не голосует.',
        "night_prompt_doktor": '🩺 <b>Ночь.</b> Кого вылечить?',
        "night_prompt_doktor_last": '\n⚠️ Нельзя лечить {name} две ночи подряд.',
        "night_prompt_potrashitel": '🔪 <b>Ночь.</b> В кого стрелять? (умирают только носители ролей)',
        "night_prompt_manyak": '🧠 <b>Ночь.</b> Кого убить?',
        "night_prompt_jurnalist": '📰 <b>Ночь.</b> Выберите первого человека.',
        "pick_second": 'Выберите второго человека:',
        "sheriff_check_blocked": '🔍 Этой ночью проверить не удалось (защита красотки).',
        "sheriff_check_mafia": '🔍 {name} — <b>мафия</b>.',
        "sheriff_check_not": '🔍 {name} — <b>не мафия</b>.',
        "sergeant_watch": '🎖️ Шериф проверил {name}.{extra}',
        "sergeant_mafia": ' (результат: мафия)',
        "sergeant_not_mafia": ' (результат: не мафия)',
        "sergeant_blocked": ' (нет результата из‑за защиты)',
        "sheriff_you_now": '🎖️ Шериф погиб. Теперь <b>вы новый шериф</b>.',
        "sergeant_now_sheriff": '🎖️ Сержант стал новым шерифом.',
        "journalist_blocked": 'Этой ночью сведений нет (защита красотки).',
        "journalist_same": '📰 {a} и {b}: <b>роли одинаковые</b>.',
        "journalist_diff": '📰 {a} и {b}: <b>роли разные</b>.',
        "potrashitel_immune": '🔪 Пуля не взяла. У этой цели нет роли, чувствительной к выстрелу.',
        "yakudza_prompt": '🥋 Вы погибли, но наносите последний удар. Кого убить? (100%)',
        "yakudza_dm_fail": 'Якудза не смог написать в личку — мести не было.',
        "game_not_found": 'Игра не найдена.',
        "not_revenge_time": 'Сейчас не время мести.',
        "revenge_skipped": 'Месть пропущена',
        "revenge_skipped_long": 'Месть пропущена.',
        "revenge_ok": 'Месть принята',
        "revenge_ok_long": '✅ Месть принята.',
        "yakudza_kill": '🥋 Месть якудзы: {name} погиб(ла) — {role}.',
        "bad_role": 'Неверная роль.',
        "bot_started": 'Бот запущен',
        "too_many_requests": 'Слишком много запросов. Подождите.',
        "cmd_start": 'О боте',
        "cmd_help": 'Помощь',
        "cmd_rules": 'Правила ролей',
        "cmd_game": 'Начать игру',
        "cmd_extend": 'Продлить набор',
        "cmd_stop": 'Остановить игру',
        "cmd_settings": 'Настройки группы',
        "cmd_stats": 'Статистика',
        "cmd_rating": 'Рейтинг',
        "cmd_addadmin": 'Добавить в штаб',
        "cmd_deladmin": 'Убрать из штаба',
        "cmd_gif_night": 'Сменить GIF ночи',
        "cmd_gif_day": 'Сменить GIF утра',
        "cmd_cancel": 'Отменить смену GIF',
        "test_someone": "кто-то",
        "test_talk_wrap": "💬 <b>{name}</b>: {text}",
        "test_talk": (
            "Мне не нравится, как себя ведёт {name}.\n"
            "Давайте не торопиться. Ночь была странная.\n"
            "Я мирный, мне скрывать нечего.\n"
            "Комиссар, если ты жив — дай зацепку.\n"
            "{name} слишком тихо себя ведёт. Подозрительно.\n"
            "Может, повесим {name}? Или рано?\n"
            "Доктор, не спи, нас мало осталось.\n"
            "Мафия сейчас явно давит на одного.\n"
            "Я бы не голосовал за первого попавшегося.\n"
            "Кто-нибудь видел, кто врёт в глазах?\n"
            "{name}, оправдайся. Почему молчишь?\n"
            "Если комиссар стрелял — скажи, в кого.\n"
            "Мне кажется, {name} играет слишком уверенно.\n"
            "Город, не вешайте своих. Подумайте.\n"
            "У меня плохое чувство насчёт {name}.\n"
            "Давайте сначала выслушаем всех.\n"
            "Ночью кто-то явно целился не туда.\n"
            "Я голосую головой, не эмоциями.\n"
            "{name} вчера тоже странно себя вёл.\n"
            "Если это мафия — они сейчас будут нас сталкивать."
        ),
        "btn_skip": "⏭ Пропустить",
        "btn_check": "🔍 Проверить",
        "btn_kill": "🔫 Убить",
        "btn_yes": "✅ Да, казнить",
        "btn_no": "❌ Нет",
        "role_aholi": "👨🏼 Мирный житель",
        "role_krosniy_otets": "🤵 Дон",
        "role_mafiya": "🤵 Мафия",
        "role_sherif": "🕵️ Комиссар Катани",
        "role_serjant": "💂 Сержант",
        "role_doktor": "👨‍⚕️ Доктор",
        "role_manyak": "🔪 Маньяк",
        "role_krasotka": "💃 Красотка",
        "role_potrashitel": "💂 Потрашитель",
        "role_jurnalist": "📰 Журналист",
        "role_yakudza": "🤞 Якудза",
        "alert_aholi": "Вы — 👱 Мирный житель!\nНет особой силы. Днём голосуйте и защищайте город.",
        "alert_krosniy_otets": "Вы — 🤵 Крёстный отец!\nГлава мафии. Ночью побеждает большинство; при ничьей решаете вы.",
        "alert_mafiya": "Вы — 🤵 Мафия!\nНочью вместе убиваете 1 игрока. Голоса видны команде, ничью решает Дон.",
        "alert_sherif": "Вы — 🕵️ Шериф!\nНочью проверяете или убиваете. Ответ: Мафия / Не мафия.",
        "alert_serjant": "Вы — 👮 Сержант!\nВидите ходы шерифа. Если шериф умрёт — станете шерифом.",
        "alert_doktor": "Вы — 👨‍⚕️ Доктор!\nНочью лечите 1 игрока. Нельзя лечить одного дважды подряд. Маньяка/потрашителя не спасаете.",
        "alert_manyak": "Вы — 🔪 Маньяк!\nКаждую ночь убиваете 1. Доктор вас не спасает. Побеждаете в одиночку.",
        "alert_krasotka": "Вы — 💃 Красотка!\nНочью блокируете 1 игрока: его не трогают, он не голосует. Если выберете Отца — мафия не убивает.",
        "alert_potrashitel": "Вы — 🔪 Потрашитель!\nЗа город. Убиваете только ролевых. Житель и Якудза не умирают.",
        "alert_jurnalist": "Вы — 📰 Журналист!\nНочью сравниваете двоих: оба мафия или нет — одинаковые / разные.",
        "alert_yakudza": "Вы — 🥋 Якудза!\nКак мирный. Если вас повесят или убьют ночью, вы 100% убиваете 1 игрока.",
        "card_aholi": "👱 <b>Мирный житель</b>\nНет особой силы. Днём голосуете за город.",
        "card_krosniy_otets": "🤵 <b>Крёстный отец</b>\nГлава мафии. Ночью побеждает большинство; ничью решаете вы. Если Красотка выберет вас — мафия не убивает.",
        "card_mafiya": "🤵 <b>Мафия</b>\nНочью вместе убиваете 1. Голоса видны в личке. Ничью решает Дон.",
        "card_sherif": "🕵️ <b>Шериф</b>\nНочью проверка или убийство. Ответ: Мафия / Не мафия. Маньяк — не мафия.",
        "card_serjant": "👮 <b>Сержант</b>\nВидите проверки/выстрелы шерифа. После смерти шерифа становитесь шерифом.",
        "card_doktor": "👨‍⚕️ <b>Доктор</b>\nНочью лечите себя или 1 игрока. Нельзя одного дважды подряд. Не спасает от маньяка и ролевого потрашителя.",
        "card_manyak": "🔪 <b>Маньяк</b>\nОдиночка. Каждую ночь 1 жертва. Доктор не спасает.",
        "card_krasotka": "💃 <b>Красотка</b>\nБлокирует 1 игрока (кроме выстрела потрашителя/комиссара). Он не голосует днём. Дон — мафия не убивает. Вас ночью могут убить только комиссар или потрашитель.",
        "card_potrashitel": "🔪 <b>Потрашитель</b>\nЗа город. Убивает только роли. Якудза и мирный не умирают.",
        "card_jurnalist": "📰 <b>Журналист</b>\nДвое ночью: 1 мафия + 1 другой → разные; обе мафии или обе нет → одинаковые.",
        "card_yakudza": "🥋 <b>Якудза</b>\nЗа город, как мирный. При смерти 100% убивает 1 игрока.",
    },
    "en": {
        "start": "Hello!\nI am the 🤵🏻 official Mafia game bot.",
        "btn_add_group": "🤵🏻 Add bot to a group ↗️",
        "btn_join_group": "🎲 Join the group",
        "btn_language": "🇬🇧 Language / Til",
        "btn_profile": "👤 Profile",
        "btn_roles": "🎭 Roles",
        "btn_stats": "📊 Statistics",
        "btn_rating": "🏆 Rating",
        "btn_close": "❌ Close",
        "btn_shop": "🛒 Shop",
        "btn_market": "🎁 Market",
        "btn_profile_app": "👤 Profile",
        "btn_topup": "💳 Top up",
        "btn_buy_money": "Buy 💵",
        "btn_buy_gems": "Buy 🪙",
        "btn_buy_vcoin": "Buy 🪙",
        "btn_use": "✅ Use",
        "btn_armed": "⏳ Next game",
        "btn_pick_role": "🎭 Pick role",
        "btn_stars": "⭐ Vcoin",
        "shop_soon": "Shop coming soon.",
        "shop_title": "<b>Shop</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_header": "<b>Shop</b>\n💵 {money} · 🪙 {vcoin}\n🛡️ {protection} · 📁 {documents} · 🎎 {active_role} · 🎭 {chosen_role}",
        "shop_item_line": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_item_card": "{emoji} <b>{title}</b>\n{desc}\n{price}",
        "shop_price_money": "💵 {n}",
        "shop_price_vcoin": "🪙 {n}",
        "shop_empty": "No items yet.",
        "shop_bought": "Bought: {item}",
        "shop_broke": "Not enough funds.",
        "shop_missing": "Item not found.",
        "shop_off": "This item is disabled.",
        "shop_no_price": "This item has no price.",
        "shop_used": "Will apply in the next game: {item}",
        "shop_already": "Already set for the next game.",
        "shop_need_item": "Buy it first.",
        "shop_need_pick": "Pick a role first.",
        "shop_role_saved": "Chosen role: {role}",
        "shop_pick_title": "Which role do you want?",
        "shop_armed_line": "Next game: {items}",
        "shop_pick_now": "Selected: {role}",
        "role_active_public": "🎎 Active role",
        "protect_fired": "Someone's protection triggered!",
        "stars_title": "<b>Vcoin packs</b>\nPay with Telegram Stars.",
        "stars_invoice": "{n} Vcoin",
        "stars_desc": "VolMafia Vcoin",
        "stars_ok": "+{n} Vcoin added.",
        "stars_off": "Stars payments are unavailable right now.",
        "gift_ok": "Order received. An admin will contact you.",
        "gift_broke": "Not enough Vcoin.",
        "gift_missing": "Gift not found.",
        "gift_busy": "Wait for previous orders to be fulfilled.",
        "shop_boost_fail_chosen": "That role is not in this game. The charge was kept.",
        "shop_boost_fail_active": "An active role could not be given. The charge was kept.",
        "gift_done_dm": "🎁 Your order was fulfilled: {title}",
        "gift_cancel_dm": "🎁 Order cancelled. 🪙 {n} Vcoin refunded.",
        "gift_admin": "🎁 New order #{id}\n{name} (<code>{uid}</code>) {user}\n{emoji} {title}\n🪙 {vcoin}",
        "market_need_https": "Mini App Market needs HTTPS in PANEL_PUBLIC_URL.",
        "market_tab_gifts": "🎁 Gifts",
        "market_tab_boosts": "🎎 Game",
        "market_tab_stars": "⭐ Vcoin",
        "market_tab_swap": "💵 $",
        "market_empty_gifts": "No gifts are listed right now.",
        "market_empty_shop": "No items.",
        "market_empty_packs": "No packs.",
        "market_empty_swap": "No exchange offers.",
        "market_confirm_gift": "Spend {n} Vcoin on {title}? An admin will send it by hand.",
        "market_confirm_swap": "Exchange {v} Vcoin for {m}$?",
        "market_swap_ok": "+{m}$ · −{v} Vcoin",
        "market_swap": "Exchange",
        "market_swap_hint": "Exchange Vcoin for regular $. Top-up is separate.",
        "market_auth": "Open Market from the Telegram Mini App.",
        "market_error": "Something went wrong. Try again.",
        "market_bought": "Purchased.",
        "market_used": "Set for the next game.",
        "market_add": "Add",
        "market_buy": "Buy",
        "market_close": "Close",
        "app_profile": "Profile",
        "app_topup": "Top up",
        "topup_pick": "Choose a payment method",
        "topup_kind": "What do you want to top up?",
        "pay_stars": "⭐ Telegram Stars",
        "pay_stars_desc": "Buy Vcoin with Telegram Stars.",
        "pay_market": "🎁 Market",
        "pay_market_desc": "You can also top up through Market.",
        "pay_vcoin": "🪙 Vcoin",
        "pay_vcoin_desc": "Buy Vcoin with Telegram Stars.",
        "pay_money": "💵 Money ($)",
        "pay_money_desc": "Buy $ with Telegram Stars.",
        "profile_games": "Games",
        "profile_wins": "Wins",
        "profile_inv": "Inventory",
        "profile_empty_inv": "Inventory is empty.",
        "profile_badges": "Badges",
        "profile_badges_empty": "No badges yet.",
        "topup_hint": "Pick a method, then a pack.",
        "topup_hint_kind": "Pick Vcoin or $, then a pack.",
        "stars_ok_money": "+{n}$ added.",
        "stars_invoice_money": "{n}$",
        "stars_desc_money": "VolMafia $",
        "maintenance": "The bot is in maintenance. Try later.",
        "user_banned": "You cannot play.",
        "group_banned": "Games are blocked in this group.",
        "join_banned": "You are banned.",
        "staff_not_super": "Super-admin only.",
        "staff_wait": "Send a user ID or forward a message.",
        "staff_need_user": "Need a user ID or a reply.",
        "staff_pick": "Pick a role for {name} (<code>{id}</code>).",
        "staff_added": "Added to staff: <code>{id}</code> — {role}",
        "staff_removed": "Removed from staff: <code>{id}</code>",
        "staff_env": "ENV admins cannot be removed.",
        "staff_cancelled": "Cancelled.",
        "staff_only": "This section is for admins only.",
        "staff_role_super": "👑 Super",
        "staff_role_moderator": "🛡️ Moderator",
        "staff_role_ads": "📣 Ads",
        "btn_back": "🔙 Back",
        "roles_title": "<b>Available roles</b>\nTap a role name to see its description",
        "lang_title": "Choose language / Tilni tanlang:",
        "lang_pick_first": (
            "🌐 Tilni tanlang\n"
            "Выберите язык\n"
            "Choose language"
        ),
        "lang_uz": "🇺🇿 O'zbekcha",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "lang_saved": "Language changed: English",
        "profile_text": (
            "👤 {username}\n"
            "💵 Money: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Protection: {protection}\n"
            "📁 Documents: {documents}\n"
            "🎎 Active role: {active_role}\n"
            "🎭 Chosen role: {chosen_role}"
        ),
        "profile_body": (
            "👤 {username}\n"
            "💵 Money: {money}\n"
            "🪙 Vcoin: {vcoin}\n"
            "\n"
            "🛡️ Protection: {protection}\n"
            "📁 Documents: {documents}\n"
            "🎎 Active role: {active_role}\n"
            "🎭 Chosen role: {chosen_role}"
        ),
        "profile_win_header": (
            "<b>Game over</b>\n"
            "For winning as \"{role}\" you received 💵 {amount}!"
        ),
        "profile_reward_header": (
            "<b>Game over</b>\n"
            "For the \"{role}\" role you received 💵 {amount}!"
        ),
        "group_settings": (
            "⚙️ <b>Group settings</b>\n\n"
            "🌐 Language: {lang_name}\n"
            "▶️ Auto-start: {auto}"
        ),
        "group_lang_admin": "Only a group admin can change the language.",
        "group_settings_admin": "Only a group admin can change settings.",
        "auto_on": "on",
        "auto_off": "off",
        "auto_enabled": "Auto-start turned on.",
        "auto_disabled": "Auto-start turned off.",
        "btn_auto_on": "✅ Auto-start: on",
        "btn_auto_off": "❌ Auto-start: off",
        "reg_wait_start": "⏳ Signup time is over. Auto-start is off — start the game with /start.",
        "no_group_link": "The play-group link is not set yet.",
        "help_private": (
            "🎭 I host <b>Mafia</b> in group chats.\n\n"
            "1) Add the bot to a group and make it <b>admin</b>.\n"
            "2) Type /game in the group.\n"
            "3) Press /start here first, then join.\n"
            "4) 🛒 Shop — protection/documents ($), active/chosen role (Vcoin).\n"
            "5) 🎁 Market — real gifts for Vcoin."
        ),
        "help_group": (
            "🎭 <b>Commands</b>\n"
            "/game — open signup\n"
            "/start — start the game\n"
            "/extend — extend signup\n"
            "/stop — stop the game\n"
            "/exit — suicide / leave the game\n"
            "/game-test N — test (bots, admin only)\n"
            "/settings — group settings\n"
            "/qoidalar — roles"
        ),
        "btn_join": "✅ Join",
        "join_ok": "You successfully joined the game {group}",
        "join_already": "Be patient, you are in the game! Got it? In the game! :)",
        "join_closed": "Signup is closed.",
        "join_full": "No seats left.",
        "join_other": "You are already in another game.",
        "join_not_found": "Game not found. Type /game in the group.",
        "btn_leave": "❌ Leave",
        "btn_start_game": "▶️ Start game",
        "btn_group_lang": "🌐 Language",
        "reg_already": "Signup is already open.",
        "game_already": "A game is already running in this group.",
        "test_usage": (
            "🧪 Test: <code>/game-test 8</code>\n"
            "Signup like a real game. N is total players (humans + bots), {min}–{max}."
        ),
        "test_admin_only": "Only a group admin or bot admin can start test mode.",
        "test_pick_role": (
            "🧪 <b>Test mode</b>\n"
            "Players: <b>{n}</b> (you + {bots} bots)\n\n"
            "Pick your role. The rest are assigned to bots at random.\n"
            "Bots play in Russian. Stats are not recorded."
        ),
        "test_pick_role_dm": (
            "🧪 <b>Test.</b> Pick your role.\n"
            "Only you see this choice. You can change it before start.\n"
            "If you skip, a random role is assigned at start."
        ),
        "test_role_picked": (
            "🧪 You chose {role}.\n"
            "You can change it with another button before the game starts."
        ),
        "test_role_taken": "That role is taken. Pick another.",
        "test_started": (
            "🧪 <b>Test started.</b> Humans: {humans}, bots: {bots}.\n"
            "Bots will chat in Russian and take night/vote actions themselves. Stats are not recorded."
        ),
        "test_setup_timeout": "🧪 Test cancelled — no role was chosen.",
        "test_not_setup": "It is not time to pick a test role.",
        "test_only_host": "Only the person who started the test can pick a role.",
        "test_pick_pending": "Pick a test role first, or /stop.",
        "test_reg_text": (
            "🧪 <b>Test Mafia</b>\n\n"
            "Signup is open (like a real game).\n"
            "Humans: <b>{n}/{max}</b>\n"
            "Bots added at start: <b>{bots}</b>\n\n"
            "Pick your role in the bot’s private chat — it is personal.\n\n"
            "{players}"
        ),
        "reg_text": (
            "🎭 <b>Mafia game</b>\n\n"
            "Signup is open.\n"
            "Players: <b>{n}/{max}</b> (minimum {min})\n\n"
            "{players}"
        ),
        "reg_empty": "Nobody yet",
        "need_admin": "⚠️ Make the bot admin: delete messages and restrict members.",
        "game_started": (
            "<b>The game has started!</b>\n\n"
            "All volunteers can view their roles."
        ),
        "btn_view_role": "🎭 View role",
        "btn_open_bot": "Open bot ↗️",
        "btn_vote": "🗳 Vote",
        "night_intro": (
            "🌃 <b>Night</b>\n"
            "Only the brave walked the streets. At dawn we count the living..."
        ),
        "night_living": (
            "<b>Alive players:</b>\n{living}\n\n"
            "{seconds} sec until dawn"
        ),
        "day_intro": (
            "🏙 <b>Day {n}</b>\n"
            "The sun rose and dried the blood spilled at night..."
        ),
        "day_living": (
            "<b>Alive players:</b>\n{living}\n\n"
            "<b>Among them:</b>\n{roles}\n"
            "Total: {n} players.\n\n"
            "Time to discuss what happened at night..."
        ),
        "vote_group": (
            "Time to find the guilty and punish them.\n"
            "{seconds} seconds to vote"
        ),
        "vote_dm": "Time to find the guilty!\nWho do you want to hang?",
        "vote_dm_picked": (
            "Time to find the guilty!\n"
            "Who do you want to hang?\n\n"
            "You chose {name}"
        ),
        "flavor_manyak": "🔪 The maniac hid in the bushes...",
        "flavor_sheriff_kill": "🕵️ Commissioner Katani loaded his pistol...",
        "flavor_sheriff_check": "🕵️ Commissioner Katani went hunting villains...",
        "flavor_mashuqa": "💃 Lady is waiting for a guest...",
        "flavor_mafia": "🤵 Mafia chose a victim...",
        "flavor_doctor": "👨‍⚕️ The doctor went on night duty...",
        "flavor_padrajitel": "💂 The hitman chose someone...",
        "flavor_journalist": "📰 The journalist is questioning people...",
        "night_kill": "At night {role} {name} was brutally killed...",
        "night_kill_cause": "They say {killer} visited them",
        "not_in_game": "You are not in this game.",
        "start_need_players": "Need at least {min} players to start. Now: {n}.",
        "your_role": "Your role:\n\n{card}",
        "mafia_team": "🔫 <b>Mafia team:</b>",
        "mafia_mates_title": "🔫 Remember the mafia members:",
        "mafia_mate_line": "• {name} - {role} 🤵",
        "mafia_label_don": "Don",
        "mafia_label_mafiya": "Mafia",
        "mafia_vote_arrow": "🤵 {role} ({voter}) --> {target}",
        "mafia_kill_decided": "The mafia has decided to kill {name} tonight!",
        "mafia_change_prompt": "🔫 Who do we kill?",
        "btn_change_vote": "🔄 Change vote",
        "mafia_chat_hint": (
            "💬 Message the bot in private — living mafia will see it. "
            "At night the team sees who voted for whom."
        ),
        "mafia_chat_hint_short": "💬 Write in private — mafia can read it.",
        "mafia_pm": "{name}: {text}",
        "mafia_night_prompt": "🔫 <b>Night.</b> Who do we kill?",
        "mafia_night_prompt_don": "👔 <b>Night.</b> Who do we kill?",
        "mafia_vote_change_hint": "You can change your vote with another button.",
        "mafia_vote_cast": "{voter} → voted for {target}",
        "mafia_vote_cast_skip": "{voter} skipped the vote",
        "mafia_votes_header": "🔫 <b>Mafia votes:</b>",
        "mafia_vote_item": "• {voter} → {target}",
        "mafia_vote_pending": "• {name} — waiting",
        "mafia_vote_skip_line": "• {name} — skipped",
        "mafia_vote_leader": "Leader: {name} ({n})",
        "mafia_vote_tie_don": "Tie: {names}. Don's pick: {name}",
        "mafia_vote_tie_wait": "Tie: {names}. The Don decides.",
        "mafia_vote_none": "No votes yet.",
        "you_mark": " ← you",
        "boss_mark": " (Godfather)",
        "night_public": (
            "🌙 <b>Night {n}</b>\n\n"
            "<b>Alive players:</b>\n{living}\n\n"
            "{roles}"
        ),
        "remaining_roles_title": "Roles still in the game:",
        "day_public": "☀️ <b>Day {n}</b>\n\n{report}\n\n<b>Alive players:</b>\n{living}\n\nDiscuss. ⏳ {seconds} sec",
        "vote_public": "🗳 <b>Vote</b>\nWho do we hang?{blocked}\n\n{living}\n\n⏳ {seconds} sec",
        "krasotka_no_vote": "\n💄 {name} cannot vote today (beauty).",
        "confirm_public": "Do you really want to hang {name}?",
        "confirm_closed": "Do you really want to hang {name}?\n\nVoting has ended",
        "lynch_hang_result": (
            "Vote results:\n"
            "{yes} 👍  |  {no} 👎\n\n"
            "{name} - we hang them! :)"
        ),
        "lynch_was_role": "{name} was {role}",
        "lynch_no_agree": (
            "The town could not agree ({yes} 👍 | {no} 👎 )... "
            "Because of the deadlock nobody was hanged..."
        ),
        "vote_cast": "{voter} voted for {target}",
        "vote_cast_skip": "{voter} skipped the vote",
        "killers_two": "{a} and {b}",
        "night_pick": "You chose {name}.",
        "night_pick_kill": "You chose to kill {name}.",
        "night_pick_check": "You chose to check {name}.",
        "win_side_town": "Town",
        "win_side_mafia": "Mafia",
        "win_side_manyak": "Killer",
        "end_title": "The game is over!",
        "end_winner_side": "Winner: {side}",
        "end_winners_title": "Winners:",
        "end_others_title": "Other players:",
        "end_duration": "The game lasted {duration}",
        "new_don": "New don - {name}",
        "new_don_dm": "🤵 You are the new Don.",
        "stats_global": (
            "📊 <b>Bot statistics</b>\n\n"
            "Games: <b>{games}</b>\n"
            "Players: <b>{players}</b>\n"
            "Rewards: <b>{money}$</b>"
        ),
        "stats_group": (
            "📊 <b>Group statistics</b>\n\n"
            "Games: <b>{games}</b>\n"
            "Town: <b>{town}</b>\n"
            "Mafia: <b>{mafia}</b>\n"
            "Killer: <b>{manyak}</b>\n"
            "Rewards: <b>{money}$</b>"
        ),
        "rating_title_global": "🏆 <b>Global rating</b>",
        "rating_title_group": "🏆 <b>Group rating</b>",
        "rating_line": "{n}. {name} — {money}$",
        "rating_you": "Your place: <b>#{rank}</b> ({money}$)",
        "rating_unranked": "You are not on the rating yet.",
        "rating_empty": "The rating is empty.",
        "rank_dash": "—",
        "duration_ms": "{m} min. {s} sec.",
        "duration_hms": "{h} h {m} min. {s} sec.",
        "vote_line": "{voter} → {target}",
        "vote_line_skip": "{voter} → skip",
        "vote_self": "You cannot vote for yourself.",
        "vote_dead": "Dead players cannot vote.",
        "vote_nominee": "The nominated player cannot vote on their own hanging.",
        "vote_already": "You have already voted.",
        "vote_blocked": "You cannot vote today.",
        "vote_not_now": "It is not voting time.",
        "vote_accepted": "Vote recorded",
        "not_in_this_game": "You are not in the game.",
        "confirm_not_now": "It is not confirmation time.",
        "confirm_accepted": "Accepted",
        "confirm_group_only": "Hanging votes are only accepted in the group.",
        "lynch_rejected": "The hanging was not confirmed.",
        "lynch_score_yes": "Score {yes}-{no} and the town decided to hang {name} ☠️",
        "lynch_score_tie": (
            "Score {yes}-{no} tie. The town could not reach a decision. "
            "So you live for now"
        ),
        "lynch_score_no": (
            "Score {yes}-{no}. The town could not reach a decision. "
            "So you live for now"
        ),
        "afk_death": "{name} fell asleep and died.",
        "suicide_death": (
            "{name} could not bear the evil in this city and hanged themselves ☠️"
        ),
        "admin_removed": "⚖️ An admin removed {name} from the game.",
        "exit_not_in_game": "You are not in a game right now.",
        "exit_already_dead": "You are already dead.",
        "exit_not_now": "/exit is not available now.",
        "sheriff_promoted": "🎖️ {name} is now the sheriff!",
        "sheriff_promoted_dm": "🎖️ You are the new sheriff.",
        "city_sleeps": "The city falls asleep...",
        "vote_who": "🗳 Who do we hang?",
        "confirm_ask_dm": "⚖️ Hang {name}?",
        "death_line": "💀 {name} died — {role}",
        "night_none": "Nobody died at night.",
        "night_some": "At night:\n{lines}",
        "lynch": "🕯 The city hanged {name}. Role: {role}",
        "no_lynch": "No hanging. The city falls asleep...",
        "votes_title": "Votes:",
        "vote_skip": "Skip",
        "no_votes": "Nobody voted.",
        "win_town": "🏆 <b>Town wins!</b> Mafia and the maniac are gone.",
        "win_mafia": "🏆 <b>Mafia wins!</b> The city has fallen.",
        "win_manyak": "🏆 <b>Maniac wins!</b> Only the killer remains.",
        "game_over": "Game over.",
        "reveal_title": "🃏 <b>Roles:</b>",
        "game_stopped": "⛔ Game stopped.",
        "gif_admin_only": "This command is for admins only.",
        "gif_send_tun": "Send the night GIF. Cancel: /cancel",
        "gif_send_tong": "Send the dawn GIF. Cancel: /cancel",
        "gif_saved_tun": "✅ Night GIF saved. It will be used every night.",
        "gif_saved_tong": "✅ Dawn GIF saved. It will be used at the start of every day.",
        "gif_need_gif": "Send a GIF (not a photo). Cancel: /cancel",
        "gif_cancelled": "GIF change cancelled.",
        "no_reg": 'Signup is not open.',
        "only_host_admin": 'Only the host or an admin.',
        "reg_extended": '⏳ Signup extended by {seconds} seconds.',
        "no_game_now": 'No game.',
        "cannot_leave_now": 'You cannot leave right now.',
        "not_on_list": 'You are not on the list.',
        "host_cannot_leave": 'The host cannot leave. Stop the game with /stop.',
        "left_ok": 'You left.',
        "cannot_start_now": 'The game cannot start now.',
        "only_host_start": 'Only the host can press start.',
        "need_n_players": 'At least {n} players are required.',
        "starting": 'Starting the game...',
        "game_cancelled_min": 'Game cancelled — at least {n} players are required.',
        "dm_role_failed": '⚠️ {name} has not opened the bot DM — the role may not have arrived.',
        "bad_button": 'Invalid button.',
        "not_night": 'It is not night.',
        "cannot_act": 'You cannot act.',
        "not_sheriff": 'You are not the sheriff.',
        "skipped": 'Skipped',
        "move_skipped": '⏭ Move skipped.',
        "bad_choice": 'Invalid choice.',
        "sheriff_check_who": 'Who do you check?',
        "sheriff_kill_who": 'Who do you kill?',
        "bad_target": 'Invalid target.',
        "not_journalist": 'You are not the journalist.',
        "pick_two_people": 'Pick two different people.',
        "not_your_move": 'This is not your move.',
        "already_acted": 'You already acted.',
        "cannot_self": 'You cannot pick yourself.',
        "doctor_no_repeat": 'You cannot heal the same person two nights in a row.',
        "night_prompt_sheriff": '🕵️ <b>Night.</b> Check or kill?',
        "night_prompt_krasotka": '💄 <b>Night.</b> Who do you block? They cannot vote tomorrow.',
        "night_prompt_doktor": '🩺 <b>Night.</b> Who do you heal?',
        "night_prompt_doktor_last": '\n⚠️ You cannot heal {name} two nights in a row.',
        "night_prompt_potrashitel": '🔪 <b>Night.</b> Who do you shoot? (only role-holders die)',
        "night_prompt_manyak": '🧠 <b>Night.</b> Who do you kill?',
        "night_prompt_jurnalist": '📰 <b>Night.</b> Pick the first person.',
        "pick_second": 'Pick the second person:',
        "sheriff_check_blocked": '🔍 The check failed tonight (beauty protection).',
        "sheriff_check_mafia": '🔍 {name} — <b>Mafia</b>.',
        "sheriff_check_not": '🔍 {name} — <b>Not mafia</b>.',
        "sergeant_watch": '🎖️ The sheriff checked {name}.{extra}',
        "sergeant_mafia": ' (result: mafia)',
        "sergeant_not_mafia": ' (result: not mafia)',
        "sergeant_blocked": ' (no result because of protection)',
        "sheriff_you_now": '🎖️ The sheriff died. <b>You are the new sheriff</b>.',
        "sergeant_now_sheriff": '🎖️ The sergeant is now sheriff.',
        "journalist_blocked": 'No info tonight (beauty protection).',
        "journalist_same": '📰 {a} and {b}: <b>same roles</b>.',
        "journalist_diff": '📰 {a} and {b}: <b>different roles</b>.',
        "potrashitel_immune": '🔪 The shot did nothing. That person has no role the hitman can kill.',
        "yakudza_prompt": '🥋 You died, but you land the last hit. Who do you kill? (100%)',
        "yakudza_dm_fail": 'Could not DM the yakuza — no revenge.',
        "game_not_found": 'Game not found.',
        "not_revenge_time": 'It is not revenge time.',
        "revenge_skipped": 'Revenge skipped',
        "revenge_skipped_long": 'Revenge skipped.',
        "revenge_ok": 'Revenge accepted',
        "revenge_ok_long": '✅ Revenge accepted.',
        "yakudza_kill": '🥋 Yakuza revenge: {name} died — {role}.',
        "bad_role": 'Invalid role.',
        "bot_started": 'Bot started',
        "too_many_requests": 'Too many requests. Please wait.',
        "cmd_start": 'About the bot',
        "cmd_help": 'Help',
        "cmd_rules": 'Role rules',
        "cmd_game": 'Start a game',
        "cmd_extend": 'Extend signup',
        "cmd_stop": 'Stop the game',
        "cmd_settings": 'Group settings',
        "cmd_stats": 'Statistics',
        "cmd_rating": 'Rating',
        "cmd_addadmin": 'Add staff',
        "cmd_deladmin": 'Remove staff',
        "cmd_gif_night": 'Change night GIF',
        "cmd_gif_day": 'Change day GIF',
        "cmd_cancel": 'Cancel GIF change',
        "test_someone": "someone",
        "test_talk_wrap": "💬 <b>{name}</b>: {text}",
        "test_talk": (
            "I don't like how {name} is acting.\n"
            "Let's not rush. The night was strange.\n"
            "I'm a civilian, I have nothing to hide.\n"
            "Commissioner, if you're alive — give us a hint.\n"
            "{name} is too quiet. Suspicious.\n"
            "Should we hang {name}? Or is it too early?\n"
            "Doctor, don't sleep, few of us are left.\n"
            "Mafia is clearly pushing on one person.\n"
            "I wouldn't vote for the first person we see.\n"
            "Did anyone catch a lie in someone's eyes?\n"
            "{name}, defend yourself. Why so silent?\n"
            "If the commissioner shot — say who.\n"
            "{name} is playing too confidently.\n"
            "Town, don't hang your own. Think.\n"
            "I have a bad feeling about {name}.\n"
            "Let's hear everyone first.\n"
            "Someone clearly aimed at the wrong person last night.\n"
            "I vote with my head, not emotions.\n"
            "{name} acted strangely yesterday too.\n"
            "If this is mafia — they will turn us against each other now."
        ),
        "btn_skip": "⏭ Skip",
        "btn_check": "🔍 Check",
        "btn_kill": "🔫 Kill",
        "btn_yes": "✅ Yes, hang",
        "btn_no": "❌ No",
        "role_aholi": "👨🏼 Civilian",
        "role_krosniy_otets": "🤵 Don",
        "role_mafiya": "🤵 Mafia",
        "role_sherif": "🕵️ Commissioner Katani",
        "role_serjant": "💂 Sergeant",
        "role_doktor": "👨‍⚕️ Doctor",
        "role_manyak": "🔪 Killer",
        "role_krasotka": "💃 Lady",
        "role_potrashitel": "💂 Hitman",
        "role_jurnalist": "📰 Journalist",
        "role_yakudza": "🤞 Yakuza",
        "alert_aholi": "You are the 👱 Civilian!\nNo special power. Vote by day to protect the town.",
        "alert_krosniy_otets": "You are the 🤵 Godfather!\nMafia boss. Most night votes win; you break ties.",
        "alert_mafiya": "You are 🤵 Mafia!\nKill 1 player together at night. The team sees the votes; the Don breaks ties.",
        "alert_sherif": "You are the 🕵️ Sheriff!\nCheck or kill at night. Result: Mafia / Not mafia.",
        "alert_serjant": "You are the 👮 Sergeant!\nYou see the sheriff’s actions. If the sheriff dies, you become sheriff.",
        "alert_doktor": "You are the 👨‍⚕️ Doctor!\nHeal 1 player at night. Can’t heal the same person two nights in a row. Can’t save from maniac/hitman.",
        "alert_manyak": "You are the 🔪 Maniac!\nKill 1 each night. The doctor cannot save them. You win alone.",
        "alert_krasotka": "You are the 💃 Lady!\nBlock 1 player at night: most actions fail, they can’t vote. If you pick the Don, mafia cannot kill.",
        "alert_potrashitel": "You are the 🔪 Hitman!\nTown side. You only kill role-holders. Civilian and Yakuza do not die.",
        "alert_jurnalist": "You are the 📰 Journalist!\nCompare 2 players at night: same if both mafia or both not, else different.",
        "alert_yakudza": "You are the 🥋 Yakuza!\nLooks like a civilian. If hanged or killed at night, you kill 1 player for sure.",
        "card_aholi": "👱 <b>Civilian</b>\nNo special ability. Vote for the town by day.",
        "card_krosniy_otets": "🤵 <b>Godfather</b>\nMafia boss. Most night votes win; you break ties. If Beauty picks you, mafia cannot kill.",
        "card_mafiya": "🤵 <b>Mafia</b>\nKill 1 together at night. Votes are visible in private chat. The Don breaks ties.",
        "card_sherif": "🕵️ <b>Sheriff</b>\nCheck or kill at night. Answer: Mafia / Not mafia. Maniac is not mafia.",
        "card_serjant": "👮 <b>Sergeant</b>\nSee who the sheriff checks/shoots. Become sheriff if they die.",
        "card_doktor": "👨‍⚕️ <b>Doctor</b>\nHeal yourself or 1 player. Cannot heal the same target two nights in a row. Cannot save from maniac or a role hit by the hitman.",
        "card_manyak": "🔪 <b>Maniac</b>\nLone killer. 1 kill each night. Doctor cannot save.",
        "card_krasotka": "💃 <b>Lady</b>\nBlocks 1 player (except hitman/commissioner kill). They cannot vote next day. Picking the Don stops the mafia kill. Only the commissioner or hitman can kill you at night.",
        "card_potrashitel": "🔪 <b>Hitman</b>\nTown side. Only role-holders die. Yakuza and civilians survive the shot.",
        "card_jurnalist": "📰 <b>Journalist</b>\nPick 2 at night: 1 mafia + 1 other → different; both mafia or both not → same.",
        "card_yakudza": "🥋 <b>Yakuza</b>\nTown side, looks civilian. On death, kills 1 player for sure.",
    },
}
