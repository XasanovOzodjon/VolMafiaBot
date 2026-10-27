# VolMafiaBot

Custom Mafia Telegram bot (True Mafia oqimi, o'z rollaringiz).

## Ishga tushirish

1. Redis ishlatiladi (`redis-server`).
2. `.env` yarating (`.env_simple.txt` ga qarang).
3. Virtual muhit:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

Botni guruhga qo'shib **admin** qiling (xabar o'chirish + restrict), lichkada `/start` bosing, guruhda `/game`.

## Do'kon, Vcoin, Market

- **$** — o'yin yutug'i. Ximoya va hujjatlar shu bilan.
- **Vcoin** — faol/tanlangan rol, Mini App sovg'alar, Telegram Stars paketlar. Eski tosh/gems avtomatik Vcoin.
- Lichkada **Do'kon**: sotib olish → **Ishlatish** → keyingi oddiy o'yin. Test/turnirda boost o'chiq.
- **Mini App Market**: productionda `PANEL_PUBLIC_URL` HTTPS. Lokalda `.env` da `DEBUG=true` — `python main.py` ngrok tunnel ochadi, Mini App shu HTTPS orqali ishlaydi (`ngrok` CLI kerak, `ngrok config add-authtoken ...`).
- Panel: **Iqtisod** — kim $ / Vcoin oldi yoki sarfladi.

## Admin panel

Bot ishga tushgach: http://127.0.0.1:8080/login

- Login/parol: `PANEL_LOGIN` / `PANEL_PASSWORD` (`.env_simple.txt`).
- Telegram widget faqat `PANEL_PUBLIC_URL` HTTPS bo'lsa ishlaydi.
- `ADMINS` dagi ID lar super-admin. Redis shtab rollari: super / moderator / ads.
- Guruh adminlari sozlamani o'z guruhida `/settings` orqali boshqaradi.
