from pathlib import Path
import sqlite3
import random
import time
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)
DB_PATH = Path("stock_game_db.db")


def init_db():
    if DB_PATH.exists():
        print(f"🚀 {DB_PATH} already exists.")
        return

    print(f"🚀 Building database at {DB_PATH}...")
    
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
            
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

@app.route('/')
def dashboard():
    all_stocks = get_stocks_with_growth()
    trending = sorted(all_stocks, key=lambda x: x['change_percent'], reverse=True)[:3]

    # Fetch the 3 most recently TRIGGERED news items from the server log
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT n.headline, n.effect as impact, s.symbol 
        FROM news_events ne
        JOIN News n ON ne.news_id = n.id
        JOIN stocks s ON n.stock_id = s.id
        ORDER BY ne.triggered_at DESC
        LIMIT 3
    """
    news = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()

    return render_template('dashboard.html', 
                           stocks=all_stocks, 
                           trending=trending, 
                           news=news)

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
            SELECT n.headline, n.effect as impact, s.symbol 
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # NEW QUERY: 
    # 1. Filters by TODAY
    # 2. Uses 'row_number' to only take every 5th or 10th record (keeps chart fast)
    query = """
        SELECT price, timestamp FROM (
            SELECT ph.price, ph.timestamp, 
                   ROW_NUMBER() OVER (ORDER BY ph.timestamp ASC) as row_num
            FROM price_history ph
            JOIN stocks s ON ph.stock_id = s.id
            WHERE s.symbol = ? 
              AND date(ph.timestamp, 'localtime') = date('now', 'localtime')
        )
        WHERE row_num % 5 = 0 OR row_num = 1
        ORDER BY timestamp ASC
    """
    
    history = conn.execute(query, (symbol,)).fetchall()
    conn.close()

    # If the app just started and there's no history for today yet, 
    # we return an empty list so the chart doesn't crash.
    prices = [row['price'] for row in history]
    
    return jsonify({"prices": prices})

if __name__ == "__main__":
    init_db()

    # --- START THE THREAD ---
    # This starts the function above as a 'daemon', meaning it dies when you stop app.py
    thread = threading.Thread(target=live_price_updates, daemon=True)
    thread.start()

    app.run(debug=True)