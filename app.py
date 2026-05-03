from pathlib import Path
import sqlite3
import random
import time
import threading
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
DB_PATH = Path("stock_game_db.db")


def init_db():
    if DB_PATH.exists():
        print(f"🚀 {DB_PATH} already exists.")
        return

    print(f"🚀 Building database at {DB_PATH}...")
    
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
            connection.execute("PRAGMA journal_mode=WAL;")
            
            schema_file = Path("Scripts/schema.sql") 
            seed_file = Path("Scripts/seed.sql")
            
            if schema_file.exists():
                connection.executescript(schema_file.read_text(encoding="utf-8"))
                print("📜 Schema applied.")
            
            if seed_file.exists():
                connection.executescript(seed_file.read_text(encoding="utf-8"))
                print("🌱 Seed data inserted.")
                
        print("✅ Database initialized successfully!")

    except (sqlite3.Error, Exception) as e:
        print(f"❌ Error: {e}")
        if DB_PATH.exists():
            try:
                DB_PATH.unlink()
                print("🗑️ Cleaned up corrupted database file.")
            except Exception as cleanup_err:
                print(f"⚠️ Cleanup failed: {cleanup_err}")

def live_price_updates():
    """Background engine: handles 5-second wiggles AND random news events."""
    next_news_time = time.time() + max(30, (5 * 60) + random.uniform(-300, 300))
    
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            stocks = cursor.execute("SELECT id, current_price, volatility FROM stocks").fetchall()
            for stock in stocks:
                vol = stock['volatility']
                change = random.uniform(-vol, vol)
                new_price = round(max(0.01, stock['current_price'] + change), 2)
                
                cursor.execute("UPDATE stocks SET current_price = ? WHERE id = ?", (new_price, stock['id']))
                cursor.execute("INSERT INTO price_history (stock_id, price) VALUES (?, ?)", (stock['id'], new_price))

            current_time = time.time()
            if current_time >= next_news_time:
                news_item = cursor.execute("""
                    SELECT n.id, n.effect, s.id as stock_id, s.current_price, s.symbol, n.headline
                    FROM News n
                    JOIN stocks s ON n.stock_id = s.id
                    ORDER BY RANDOM() LIMIT 1
                """).fetchone()

                if news_item:
                    multiplier = 1 + (news_item['effect'] / 100.0)
                    spiked_price = round(max(0.01, news_item['current_price'] * multiplier), 2)

                    cursor.execute("UPDATE stocks SET current_price = ? WHERE id = ?", (spiked_price, news_item['stock_id']))
                    cursor.execute("INSERT INTO price_history (stock_id, price) VALUES (?, ?)", (news_item['stock_id'], spiked_price))
                    cursor.execute("INSERT INTO news_events (news_id) VALUES (?)", (news_item['id'],))
                    
                    print(f"🚨 BREAKING NEWS: {news_item['headline']} applied to {news_item['symbol']}")

                next_news_time = time.time() + max(30, (5 * 60) + random.uniform(-300, 300))

            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Engine Error: {e}")

        time.sleep(5)

def get_stocks_with_growth():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    query = """
        SELECT 
            s.*,
            COALESCE(
                (SELECT price FROM price_history ph 
                 WHERE ph.stock_id = s.id 
                 AND date(ph.timestamp, 'localtime') = date('now', 'localtime')
                 ORDER BY ph.timestamp ASC LIMIT 1),
                s.opening_price
            ) as day_start_price
        FROM stocks s
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    stocks_list = []
    for row in rows:
        stock = dict(row)
        current = stock['current_price']
        opening = stock['day_start_price']
        
        growth = ((current - opening) / opening * 100) if (opening and opening > 0) else 0
        
        stock['change_percent'] = round(growth, 2)
        stocks_list.append(stock)
        
    return stocks_list

def get_db_news(limit=3):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        query = """
            SELECT n.headline, n.effect as impact, s.symbol 
            FROM News n
            JOIN stocks s ON n.stock_id = s.id
            ORDER BY RANDOM()
            LIMIT ?
        """
        news_rows = conn.execute(query, (limit,)).fetchall()
        conn.close()
        return [dict(row) for row in news_rows]
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        return []


@app.context_processor
def inject_user():
    if 'user_id' in session:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        return dict(user=user)
    return dict(user=None)

@app.route('/')
def dashboard():
    all_stocks = get_stocks_with_growth()
    trending = sorted(all_stocks, key=lambda x: x['change_percent'], reverse=True)[:3]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT n.headline, n.effect as impact, s.symbol, ne.triggered_at 
        FROM news_events ne
        JOIN News n ON ne.news_id = n.id
        JOIN stocks s ON n.stock_id = s.id
        ORDER BY ne.triggered_at DESC
        LIMIT 3
    """
    news = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()

    return render_template('dashboard.html', stocks=all_stocks, trending=trending, news=news)

@app.route('/stocks')
def stocks():
    all_stocks = get_stocks_with_growth()
    all_stocks = sorted(all_stocks, key=lambda x: x['symbol'])
    return render_template('stocks.html', stocks=all_stocks)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    stock = conn.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
    conn.close()

    if not stock:
        flash("Stock not found!", "danger")
        return redirect(url_for('dashboard'))

    return render_template('stock_detail.html', stock=dict(stock))

@app.route('/api/prices')
def get_prices():
    all_stocks = get_stocks_with_growth()
    stock_list = []
    for s in all_stocks:
        stock_list.append({
            "symbol": s['symbol'],
            "price": s['current_price'],
            "growth": s['change_percent']
        })
    return jsonify(sorted(stock_list, key=lambda x: x['growth'], reverse=True))

@app.route('/api/news')
def get_news_api():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT n.headline, n.effect as impact, s.symbol, ne.triggered_at 
            FROM news_events ne
            JOIN News n ON ne.news_id = n.id
            JOIN stocks s ON n.stock_id = s.id
            ORDER BY ne.triggered_at DESC
            LIMIT 3
        """
        news_rows = conn.execute(query).fetchall()
        conn.close()
        return jsonify([dict(row) for row in news_rows])
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        return jsonify([])

@app.route('/api/history/<symbol>')
def get_stock_history(symbol):
    timeframe = request.args.get('timeframe', 'all')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    if timeframe == 'today':
        query = """
            SELECT price, timestamp FROM price_history ph
            JOIN stocks s ON ph.stock_id = s.id
            WHERE s.symbol = ? 
              AND date(ph.timestamp, 'localtime') = date('now', 'localtime')
            ORDER BY ph.timestamp ASC
        """
    else:
        query = """
            SELECT price, timestamp FROM price_history ph
            JOIN stocks s ON ph.stock_id = s.id
            WHERE s.symbol = ? 
            ORDER BY ph.timestamp ASC
        """
        
    history = conn.execute(query, (symbol,)).fetchall()
    conn.close()

    line_points = [{"x": row['timestamp'], "y": row['price']} for row in history]

    candles = []
    if history:
        buckets = {}
        for row in history:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            bucket_time = dt.replace(minute=(dt.minute // 15) * 15, second=0).strftime('%Y-%m-%d %H:%M:%S')
            
            if bucket_time not in buckets:
                buckets[bucket_time] = []
            buckets[bucket_time].append(row['price'])

        for time_key, prices in buckets.items():
            candles.append({
                "x": time_key,
                "y": [ prices[0], max(prices), min(prices), prices[-1] ]
            })

    return jsonify({
        "history": line_points,
        "line": line_points,
        "candle": candles
    })


# ── TRADING API ────────────────────────────────────────────────────────────────

@app.route('/api/holdings/<symbol>')
def get_holdings(symbol):
    """Returns how many shares of a stock the logged-in user owns."""
    if 'user_id' not in session:
        return jsonify({'quantity': 0})
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    result = conn.execute("""
        SELECT p.quantity FROM portfolio p
        JOIN stocks s ON p.stock_id = s.id
        WHERE p.user_id = ? AND s.symbol = ?
    """, (session['user_id'], symbol)).fetchone()
    conn.close()
    
    return jsonify({'quantity': result['quantity'] if result else 0})


@app.route('/api/buy', methods=['POST'])
def buy_stock():
    """Buy shares: deducts cost from balance, adds to portfolio."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    symbol   = data.get('symbol', '').upper().strip()
    quantity = float(data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({'success': False, 'error': 'Quantity must be greater than zero'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        stock = conn.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
        if not stock:
            conn.close()
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        total_cost = round(stock['current_price'] * quantity, 2)
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        
        if user['balance'] < total_cost:
            conn.close()
            return jsonify({
                'success': False,
                'error': f"Insufficient funds — you need ${total_cost:,.2f} but only have ${user['balance']:,.2f}"
            }), 400
        
        # Upsert portfolio row
        existing = conn.execute(
            "SELECT id FROM portfolio WHERE user_id = ? AND stock_id = ?",
            (session['user_id'], stock['id'])
        ).fetchone()
        
        if existing:
            conn.execute(
                "UPDATE portfolio SET quantity = quantity + ? WHERE user_id = ? AND stock_id = ?",
                (quantity, session['user_id'], stock['id'])
            )
        else:
            conn.execute(
                "INSERT INTO portfolio (user_id, stock_id, quantity) VALUES (?, ?, ?)",
                (session['user_id'], stock['id'], quantity)
            )
        
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id = ?",
            (total_cost, session['user_id'])
        )
        conn.commit()
        
        new_balance  = conn.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()['balance']
        new_quantity = conn.execute(
            "SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?",
            (session['user_id'], stock['id'])
        ).fetchone()['quantity']
        conn.close()
        
        return jsonify({
            'success':      True,
            'message':      f"Bought {quantity:g} share(s) of {symbol} for ${total_cost:,.2f}",
            'new_balance':  new_balance,
            'new_quantity': new_quantity
        })
        
    except Exception as e:
        conn.close()
        print(f"❌ Buy error: {e}")
        return jsonify({'success': False, 'error': 'Server error — please try again'}), 500


@app.route('/api/sell', methods=['POST'])
def sell_stock():
    """Sell shares: adds proceeds to balance, removes from portfolio."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    symbol   = data.get('symbol', '').upper().strip()
    quantity = float(data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({'success': False, 'error': 'Quantity must be greater than zero'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        stock = conn.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
        if not stock:
            conn.close()
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        holding = conn.execute(
            "SELECT * FROM portfolio WHERE user_id = ? AND stock_id = ?",
            (session['user_id'], stock['id'])
        ).fetchone()
        
        owned = holding['quantity'] if holding else 0
        if not holding or owned < quantity:
            conn.close()
            return jsonify({
                'success': False,
                'error': f"You only own {owned:g} share(s) of {symbol}"
            }), 400
        
        total_value = round(stock['current_price'] * quantity, 2)
        
        # Remove or reduce portfolio row
        if abs(owned - quantity) < 0.0001:          # selling everything
            conn.execute(
                "DELETE FROM portfolio WHERE user_id = ? AND stock_id = ?",
                (session['user_id'], stock['id'])
            )
            new_quantity = 0.0
        else:
            conn.execute(
                "UPDATE portfolio SET quantity = quantity - ? WHERE user_id = ? AND stock_id = ?",
                (quantity, session['user_id'], stock['id'])
            )
            new_quantity = conn.execute(
                "SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?",
                (session['user_id'], stock['id'])
            ).fetchone()['quantity']
        
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (total_value, session['user_id'])
        )
        conn.commit()
        
        new_balance = conn.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()['balance']
        conn.close()
        
        return jsonify({
            'success':      True,
            'message':      f"Sold {quantity:g} share(s) of {symbol} for ${total_value:,.2f}",
            'new_balance':  new_balance,
            'new_quantity': new_quantity
        })
        
    except Exception as e:
        conn.close()
        print(f"❌ Sell error: {e}")
        return jsonify({'success': False, 'error': 'Server error — please try again'}), 500


# ── AUTH ───────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        
        flash("Invalid username or password", "danger")
    return render_template('login.html', user=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", 
                         (username, hashed_pw, 10000.0))
            conn.commit()
            conn.close()
            flash("Account created! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
            
    return render_template('login.html', register=True, user=None)

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@app.route('/api/portfolio')
def get_portfolio():
    """Returns all holdings for the logged-in user with live prices and daily P&L."""
    if 'user_id' not in session:
        return jsonify({'holdings': [], 'cash': 0}), 401

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    user = conn.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    cash = user['balance'] if user else 0

    rows = conn.execute("""
        SELECT
            s.symbol, s.name, s.current_price,
            p.quantity,
            (s.current_price * p.quantity) AS total_value,
            COALESCE(
                (SELECT price FROM price_history ph
                 WHERE ph.stock_id = s.id
                   AND date(ph.timestamp, 'localtime') = date('now', 'localtime')
                 ORDER BY ph.timestamp ASC LIMIT 1),
                s.opening_price
            ) AS day_start_price
        FROM portfolio p
        JOIN stocks s ON p.stock_id = s.id
        WHERE p.user_id = ?
        ORDER BY total_value DESC
    """, (session['user_id'],)).fetchall()
    conn.close()

    holdings = []
    for row in rows:
        r = dict(row)
        day_start = r['day_start_price'] or r['current_price']
        pct = ((r['current_price'] - day_start) / day_start * 100) if day_start else 0
        val_change = (r['current_price'] - day_start) * r['quantity']
        holdings.append({
            'symbol':          r['symbol'],
            'name':            r['name'],
            'quantity':        r['quantity'],
            'current_price':   r['current_price'],
            'total_value':     r['total_value'],
            'day_change_pct':  round(pct, 2),
            'day_change_value': round(val_change, 2),
        })

    return jsonify({'holdings': holdings, 'cash': cash})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── LEADERBOARD ────────────────────────────────────────────────────────────────

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')


@app.route('/api/leaderboard/players')
def leaderboard_players():
    """All users ranked by net worth (cash + portfolio value)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            u.id,
            u.username,
            u.balance,
            COALESCE((
                SELECT SUM(s.current_price * p.quantity)
                FROM portfolio p
                JOIN stocks s ON p.stock_id = s.id
                WHERE p.user_id = u.id
            ), 0) AS portfolio_value,
            u.balance + COALESCE((
                SELECT SUM(s.current_price * p.quantity)
                FROM portfolio p
                JOIN stocks s ON p.stock_id = s.id
                WHERE p.user_id = u.id
            ), 0) AS net_worth
        FROM users u
        ORDER BY net_worth DESC
    """).fetchall()
    conn.close()

    return jsonify({
        'players':    [dict(r) for r in rows],
        'current_id': session.get('user_id')
    })


@app.route('/api/leaderboard/campaign')
def leaderboard_campaign():
    """NPCs + the logged-in user, ranked together by net worth."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    npcs = conn.execute(
        "SELECT name, title, balance FROM npcs ORDER BY balance ASC"
    ).fetchall()

    user_net_worth = None
    if 'user_id' in session:
        row = conn.execute("""
            SELECT
                u.username,
                u.balance + COALESCE((
                    SELECT SUM(s.current_price * p.quantity)
                    FROM portfolio p
                    JOIN stocks s ON p.stock_id = s.id
                    WHERE p.user_id = u.id
                ), 0) AS net_worth
            FROM users u WHERE u.id = ?
        """, (session['user_id'],)).fetchone()
        if row:
            user_net_worth = {'username': row['username'], 'net_worth': row['net_worth']}

    conn.close()

    # Merge user into NPC list and sort
    entries = [{'name': r['name'], 'title': r['title'],
                'balance': r['balance'], 'is_npc': True} for r in npcs]

    if user_net_worth:
        entries.append({
            'name':    user_net_worth['username'],
            'title':   'That\'s you! 👋',
            'balance': user_net_worth['net_worth'],
            'is_npc':  False
        })

    entries.sort(key=lambda x: x['balance'])

    return jsonify({'entries': entries})


if __name__ == "__main__":
    init_db()

    thread = threading.Thread(target=live_price_updates, daemon=True)
    thread.start()

    app.run()