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
            
            # Using absolute paths relative to the app root is often safer in Flask
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
                # Use unlink to ensure we don't leave a broken file
                DB_PATH.unlink()
                print("🗑️ Cleaned up corrupted database file.")
            except Exception as cleanup_err:
                print(f"⚠️ Cleanup failed: {cleanup_err}")

def live_price_updates():
    """Background engine: handles 5-second wiggles AND random news events."""
    # Set the first news timer: 5 mins +/- 5 mins (min 30 seconds)
    next_news_time = time.time() + max(30, (5 * 60) + random.uniform(-300, 300))
    
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # --- 1. THE 5-SECOND PRICE WIGGLE (Your original logic) ---
            stocks = cursor.execute("SELECT id, current_price, volatility FROM stocks").fetchall()
            for stock in stocks:
                vol = stock['volatility']
                change = random.uniform(-vol, vol)
                new_price = round(max(0.01, stock['current_price'] + change), 2)
                
                cursor.execute("UPDATE stocks SET current_price = ? WHERE id = ?", (new_price, stock['id']))
                cursor.execute("INSERT INTO price_history (stock_id, price) VALUES (?, ?)", (stock['id'], new_price))

            # --- 2. SERVER-SIDE NEWS LOGIC ---
            current_time = time.time()
            if current_time >= next_news_time:
                # Grab one random piece of news
                news_item = cursor.execute("""
                    SELECT n.id, n.effect, s.id as stock_id, s.current_price, s.symbol, n.headline
                    FROM News n
                    JOIN stocks s ON n.stock_id = s.id
                    ORDER BY RANDOM() LIMIT 1
                """).fetchone()

                if news_item:
                    # Apply the impact mathematically
                    multiplier = 1 + (news_item['effect'] / 100.0)
                    spiked_price = round(max(0.01, news_item['current_price'] * multiplier), 2)

                    # Update the stock price and log the huge jump in history
                    cursor.execute("UPDATE stocks SET current_price = ? WHERE id = ?", (spiked_price, news_item['stock_id']))
                    cursor.execute("INSERT INTO price_history (stock_id, price) VALUES (?, ?)", (news_item['stock_id'], spiked_price))
                    
                    # Record that this news actually happened!
                    cursor.execute("INSERT INTO news_events (news_id) VALUES (?)", (news_item['id'],))
                    
                    print(f"🚨 BREAKING NEWS: {news_item['headline']} applied to {news_item['symbol']}")

                # Reset the timer for the next news event (5 mins +/- 5 mins)
                next_news_time = time.time() + max(30, (5 * 60) + random.uniform(-300, 300))

            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Engine Error: {e}")

        # Wait for 5 seconds before next tick
        time.sleep(5)

def get_stocks_with_growth():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # This one query handles the logic for both the Dashboard and the API
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
        
        growth = ((current - opening) / opening * 100) if opening > 0 else 0
        
        stock['change_percent'] = round(growth, 2)
        stocks_list.append(stock)
        
    return stocks_list

def get_db_news(limit=3):
    """Fetches random news items joined with their stock symbols."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # We join with stocks so we can show WHICH stock is being affected
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
    # This makes 'user' available in EVERY .html file automatically
    if 'user_id' in session:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        return dict(user=user)
    return dict(user=None)

@app.route('/')
def dashboard():
    # REMOVED the login redirect - now everyone can see this!
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
    # Fetch all stocks using your existing function
    all_stocks = get_stocks_with_growth()
    
    # Sort them alphabetically by symbol for easier browsing
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
    """API endpoint for the frontend to fetch the 3 most recently triggered news events."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # We query the new 'news_events' table to see what actually happened
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

from datetime import datetime, timedelta

@app.route('/api/history/<symbol>')
def get_stock_history(symbol):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Fetch the raw 24h data
    query = """
        SELECT price, timestamp FROM price_history ph
        JOIN stocks s ON ph.stock_id = s.id
        WHERE s.symbol = ? 
          AND ph.timestamp >= datetime('now', '-24 hours')
        ORDER BY ph.timestamp ASC
    """
    history = conn.execute(query, (symbol,)).fetchall()
    conn.close()

    # 2. Format Line Data
    line_points = [{"x": row['timestamp'], "y": row['price']} for row in history]

    # 3. Generate Candlestick Data (15-minute buckets)
    candles = []
    if history:
        # Group raw data by 15-minute intervals
        buckets = {}
        for row in history:
            # Round the timestamp down to the nearest 15 minutes
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            bucket_time = dt.replace(minute=(dt.minute // 15) * 15, second=0).strftime('%Y-%m-%d %H:%M:%S')
            
            if bucket_time not in buckets:
                buckets[bucket_time] = []
            buckets[bucket_time].append(row['price'])

        for time_key, prices in buckets.items():
            candles.append({
                "x": time_key,
                "y": [
                    prices[0],             # Open
                    max(prices),           # High
                    min(prices),           # Low
                    prices[-1]             # Close
                ]
            })

    return jsonify({
        "history": line_points,
        "line": line_points,
        "candle": candles # Now this contains actual data!
    })

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    init_db()

    # --- START THE THREAD ---
    # This starts the function above as a 'daemon', meaning it dies when you stop app.py
    thread = threading.Thread(target=live_price_updates, daemon=True)
    thread.start()

    app.run()