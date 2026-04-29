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
    """This function runs in the background forever, updating prices."""
    while True:
        try:
            # 1. Connect to the DB
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # IMPORTANT: This makes sure your ON DELETE CASCADE actually works!
            cursor.execute("PRAGMA foreign_keys = ON;")

            # 2. Get all stocks
            stocks = cursor.execute("SELECT id, current_price, volatility FROM stocks").fetchall()

            for stock in stocks:
                # 3. Calculate the 'Wiggle'
                # Formula: current + random(-vol, +vol)
                vol = stock['volatility']
                change = random.uniform(-vol, vol)
                
                # Math: New price cannot be less than $0.01
                new_price = round(max(0.01, stock['current_price'] + change), 2)

                # 4. Save back to DB
                cursor.execute(
                    "UPDATE stocks SET current_price = ? WHERE id = ?", 
                    (new_price, stock['id'])
                )

                # 5. Log price history
                cursor.execute("INSERT INTO price_history (stock_id, price) VALUES (?, ?)", (stock['id'], new_price))

            conn.commit()
            conn.close()
            
            # print(f"💹 Market Tick: Prices updated.") # Optional: Unmute for debugging
            
        except Exception as e:
            print(f"❌ live_price_updates Error: {e}")

        # 5. Wait for 5 seconds
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
    # Sort for the trending section
    trending = sorted(all_stocks, key=lambda x: x['change_percent'], reverse=True)[:3]

    # mock_news = [
    #     {'headline': 'Apple releases iToster, bread price skyrockets', 'impact': 5.2},
    #     {'headline': 'CEO of popular tech company admits he just guesses what buttons do', 'impact': -8.4},
    #     {'headline': 'Scientists discover new color, patent pending', 'impact': 1.1}
    # ]
    
    news = get_db_news()

    return render_template('dashboard.html', 
                           stocks=all_stocks, 
                           trending=trending, 
                           news=news)


@app.route('/api/prices')
def get_prices():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # NEW SQL: Same logic for the live API
    query = """
        SELECT 
            s.symbol, 
            s.current_price, 
            s.opening_price,
            (
                SELECT price 
                FROM price_history ph 
                WHERE ph.stock_id = s.id 
                  AND date(ph.timestamp, 'localtime') = date('now', 'localtime')
                ORDER BY ph.timestamp ASC 
                LIMIT 1
            ) as today_open_price
        FROM stocks s
    """
    stocks = conn.execute(query).fetchall()
    conn.close()
    
    stock_list = []
    for stock in stocks:
        current = stock['current_price']
        # Same fallback logic here
        opening = stock['today_open_price'] if stock['today_open_price'] is not None else stock['opening_price']
        
        growth = ((current - opening) / opening * 100) if opening != 0 else 0
        
        stock_list.append({
            "symbol": stock['symbol'],
            "price": round(current, 2),
            "growth": round(growth, 2)
        })
    
    sorted_stocks = sorted(stock_list, key=lambda x: x['growth'], reverse=True)
    return jsonify(sorted_stocks)

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

@app.route('/api/news')
def get_news_api():
    """API endpoint for the frontend to fetch fresh news."""
    return jsonify(get_db_news())

if __name__ == "__main__":
    init_db()

    # --- START THE THREAD ---
    # This starts the function above as a 'daemon', meaning it dies when you stop app.py
    thread = threading.Thread(target=live_price_updates, daemon=True)
    thread.start()

    app.run(debug=True)