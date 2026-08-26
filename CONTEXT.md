# VolMafia

Telegram guruhida Mafia o‘yini va lichkada iqtisod (Do‘kon, To‘ldirish, Profil).

## Language

**O‘yin**:
Guruhdagi Mafia partiyasi: ro‘yxat, tun, kun, ovoz, g‘alaba.
_Avoid_: match, session (o‘yinchi tilida)

**Do‘kon**:
Mini App katalogi: Sovg‘a, O‘yin narsasi, Almash. To‘ldirish emas.
_Avoid_: Market (o‘yinchi tugmasida Do‘kon), shop (kodda qolishi mumkin)

**To‘ldirish**:
Telegram Stars evaziga Vcoin yoki $ olish. Do‘kondan alohida sahifa.
_Avoid_: donate, deposit, topup (o‘yinchi tilida)

**$**:
O‘yin mukofoti va yumshoq valyuta. Ximoya va Hujjatlar shu bilan.
_Avoid_: so‘m, pul (matnda «Pul ($)» bo‘lishi mumkin), money (kodda)

**Vcoin**:
Premium valyuta. Faol/tanlangan rol, Sovg‘a, Almash.
_Avoid_: gem, tosh, coin (umumiy)

**Stars**:
Telegram to‘lovi. Balans emas — faqat To‘ldirish paketi narxi.
_Avoid_: XTR (o‘yinchi tilida)

**Sovg‘a**:
Real narsa. Vcoin evaziga buyurtma; admin qo‘lda yuboradi.
_Avoid_: gift shop item vs o‘yin narsasi aralashuvi

**O‘yin narsasi**:
Keyingi oddiy o‘yinga qurollanadigan narsa: Ximoya, Hujjatlar, Faol rol, Tanlangan rol.
_Avoid_: boost, item (o‘yinchi tilida)

**Almash**:
Vcoin ni $ ga almashtirish. Stars emas.
_Avoid_: exchange, convert (o‘yinchi tilida)

**Profil**:
Mini App: o‘yinchi ko‘rinishi, $ / Vcoin, statistika, inventar va Badge kolleksiyasi. Telegram lichkadagi qisqa karta faqat shu Mini Appni ochadi.
_Avoid_: account

**Badge**:
Bitta nishon, o‘yinchida **nusxa emas — Rank**. Dumaloq PNG/JPG. Olish: Shart (avto yoki matn), panel Rank, yoki Vcoin. Sotuv, panel Rank va avto-Shart $ / Vcoin bermaydi.
_Avoid_: CSS `badge`, achievement, nishon (o‘yinchi tilida Badge)

**Rank**:
Bir Badge bosqichi (1, 2, …), har birining Sharti. Skip yo‘q: Do‘kon faqat keyingi Rank; avto ham avval 1, keyin 2. Panel Rank `N` bersa, Shartsiz 1 dan N gacha to‘ldiriladi. Rankda $ mukofot yo‘q; Vcoin faqat Do‘kon narxi (0 = sotilmaydi).
_Avoid_: level, ikkinchi Badge, copy

**Shart**:
Shu Rankning matni va ixtiyoriy avto-qoida. Turlar: Play / Win / Lose; Buy (O‘yin narsasi); To‘ldirish (qoidada $ yoki Vcoin, jami faqat Stars orqali; panel / o‘yin $ / Almash kirmaydi); guruhlar (kamida M guruh × har birida N tugagan o‘yin; chiqib ketgan guruh ham). O‘yin roli va O‘yin narsasi alohida. Tekshiruv keyingi o‘yin/sotib olish/To‘ldirishda; eski hisob sanaladi. Avto pul bermaydi.
_Avoid_: task, vazifa (o‘yinchi tilida Shart)

**Sabab**:
Panelda $ / Vcoin / Badge qo‘shish yoki ayirishdagi ixtiyoriy izoh. Bo‘sh = o‘zgaradi, lichka jim. To‘ldirilsa lichkaga miqdor (yoki Badge/Rank) va Sabab — qo‘shish va ayirishda.
_Avoid_: comment, note (o‘yinchi tilida Sabab)

**Panel berish**:
Mavjud o‘yinchiga paneldan $ , Vcoin yoki Badge/Rank qo‘shish yoki ayirish. Yangi o‘yinchi yaratish emas. Sovg‘a emas. Ayirish balansni 0 dan pastga tushirmaydi (50 dan 200 ayirilsa 0).
_Avoid_: Sovg‘a, create user

**Admin mute**:
Faqat guruh admini. Reply + `mute`/`mut`/ruscha; `unmute`/`unmut`/`размут`/`анмут` — reply yoki `@username`. Muddat `m`/`h`/`d`, tavan **14 kun**. Xabar o‘chiriladi. O‘yin sukuti ustun (o‘likni yozdirmaydi). Tongda yechilmaydi.
_Avoid_: o‘yin sukuti, Admin ban

**Admin ban**:
Guruh admini, mute kabi: `ban`/`бан`/`unban`/`разбан`, reply + xabar o‘chirish, tavan 14 kun. Shu guruhdagi O‘yinga qo‘shilmaydi; chat ochiq. Joriy (test ham) O‘yindan o‘lik kabi chiqariladi. Boshqa guruh va Panel blokka tegmaydi. Guruhdan kick yo‘q.
_Avoid_: Panel blok, kick, Telegram restrict

**Panel blok**:
Panel orqali: o‘yinchini **barcha** guruhlarda o‘ynata olmaslik, yoki guruhda o‘yinni umuman yopish. Muddatsiz. Admin ban emas.
_Avoid_: Ban (guruh admini tilida Admin ban)

**O‘yin sukuti**:
Tun yoki o‘lik o‘yinchini o‘yin qoidasi bo‘yicha yozdirmaslik. Admin mute emas.
_Avoid_: mute (moderator tilida Admin mute)
