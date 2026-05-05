# 🔥 Dumpster Fire Trades

A browser-based stock trading simulation game where prices move in real time, fake news headlines shake the market, and your goal is to not lose all your fake money.

Built with Flask, SQLite, Bootstrap (Bootswatch Brite), and ApexCharts.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)

---

## What is this?

Dumpster Fire Trades is a multiplayer stock trading game for your browser. Every player starts with **$10,000** in fake money and trades 14 stocks — ranging from Bitcoin and NVIDIA to OceanGate and Hypixel Studios.

Prices tick every 5 seconds based on randomised volatility. Every few minutes a **breaking news event** fires, announcing a headline like *"Elon Musk buys Mars, SpaceX stock reaches moon literally"* — giving players a 30–90 second window to react and buy/sell before the price actually moves.

Compete against other players on the leaderboard, or climb the **Campaign ladder** by overtaking a cast of NPCs — from your neighbour's dog at $7,800, all the way up to Elon Musk at $420 billion.

---

## Features

- 📈 **Live prices** — ticking every 5 seconds with per-stock volatility
- 📰 **Delayed news events** — headlines announce 30–90s before the price impact hits
- 💹 **14 stocks** — crypto, commodities, tech, and fictional meme stocks
- 🕯️ **Line & candlestick charts** — zoomable, with zoom preserved across live updates
- 🛒 **Buy & sell** — input by shares or dollar amount, live estimated cost
- 📊 **Portfolio page** — live P&L, allocation donut chart, per-holding sparklines
- 🏆 **Player leaderboard** — ranked by net worth (cash + portfolio value)
- 🎮 **Campaign leaderboard** — beat a ladder of NPCs with increasing wealth
- 🔍 **Stock browser** — search by symbol or name, live sparklines per card
- 🔐 **Auth** — register/login with hashed passwords and CSRF protection

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Flask |
| Database | SQLite (WAL mode) |
| Frontend | Bootstrap 5.3 (Bootswatch Brite) |
| Charts | ApexCharts |
| Auth | Werkzeug password hashing |
| Background engine | Python threading |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Raitis-C/web_stock_game.git
cd web_stock_game
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up your environment file

Create a `.env` file in the project root:

```
FLASK_SECRET_KEY=some_long_random_string_here
```

You can generate a good key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run the app

```bash
python app.py
```

On first run, the database is built automatically from `Scripts/schema.sql` and `Scripts/seed.sql`. Visit `http://127.0.0.1:5000`.

---

## Project Structure

```
web_stock_game/
├── app.py                  # Flask app, routes, background price engine
├── Scripts/
│   ├── schema.sql          # Database schema
│   └── seed.sql            # Stocks, news headlines, NPCs
├── static/
│   ├── bootstrap.min.css   # Bootswatch Brite theme
│   ├── style.css           # Custom styles
│   └── Logo.png            # App logo
├── templates/
│   ├── base.html           # Navbar, footer, shared layout
│   ├── dashboard.html      # Market dashboard with trending stocks
│   ├── stocks.html         # Stock browser grid
│   ├── stock_detail.html   # Full chart + trading interface
│   ├── portfolio.html      # Holdings, P&L, allocation chart
│   ├── leaderboard.html    # Player + campaign leaderboards
│   └── login.html          # Login / register
├── .env                    # Secret key (not committed)
├── .gitignore
└── requirements.txt
```

---

## Deployment (Linux Server)

The recommended setup is **Gunicorn + Nginx** with a subdomain. A full deployment guide is below.

### Install dependencies on the server

```bash
cd /var/www
git clone https://github.com/yourname/web_stock_game.git stocks
cd stocks
python3 -m venv venv
source venv/bin/activate
pip install flask werkzeug python-dotenv gunicorn
echo "FLASK_SECRET_KEY=your_key_here" > .env
```

### Create a systemd service

`/etc/systemd/system/stocks.service`:

```ini
[Unit]
Description=Dumpster Fire Trades
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/stocks
Environment="PATH=/var/www/stocks/venv/bin"
ExecStart=/var/www/stocks/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable stocks
sudo systemctl start stocks
```

### Nginx config

`/etc/nginx/sites-available/stocks`:

```nginx
server {
    listen 80;
    server_name stocks.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/stocks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d stocks.yourdomain.com   # free HTTPS
```

---

## Adding Your Own Stocks & News

Edit `Scripts/seed.sql` — stocks and news headlines are plain SQL inserts, easy to modify. Delete `stock_game_db.db` and restart `app.py` to rebuild the database with your changes.

Volatility is the ± price swing per 5-second tick. As a rough guide:

| Asset type | Volatility range |
|---|---|
| Stable stocks | 2–5 |
| Tech / growth | 5–12 |
| Crypto | 500–2000 |
| Meme / joke stocks | anything goes |

---

## License

MIT — do whatever you want with it, just don't lose real money.
