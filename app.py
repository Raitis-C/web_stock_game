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

            conn.commit()
            conn.close()
            
            # print(f"💹 Market Tick: Prices updated.") # Optional: Unmute for debugging
            
        except Exception as e:
            print(f"❌ live_price_updates Error: {e}")

        # 5. Wait for 5 seconds
        time.sleep(5)



@app.route('/')
def dashboard():
    # Connect to the DB path object (sqlite3 accepts Path objects)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Fetch stock and news data from db
    stocks = conn.execute("SELECT * FROM stocks").fetchall()
    # news = conn.execute("SELECT * FROM News ORDER BY RANDOM() LIMIT 1").fetchone()

    # mock_stocks = [
    #     {'symbol': 'BTC', 'change': 2.54},
    #     {'symbol': 'APPL', 'change': -1.15},
    #     {'symbol': 'TSLA', 'change': 0.85}
    # ]
    
    mock_news = [
        {'headline': 'Apple releases iToster, bread price skyrockets', 'impact': 5.2},
        {'headline': 'CEO of popular tech company admits he just guesses what buttons do', 'impact': -8.4},
        {'headline': 'Scientists discover new color, patent pending', 'impact': 1.1}
    ]

    # 2. Convert to list of dicts and calculate growth
    stocks_list = []
    for row in stocks:
        stock = dict(row)
        # Calculate % change
        opening = stock['opening_price']
        current = stock['current_price']
        
        # Avoid division by zero just in case
        if opening > 0:
            growth = ((current - opening) / opening) * 100
        else:
            growth = 0
            
        stock['change_percent'] = round(growth, 2)
        stocks_list.append(stock)

    # 3. Sort by growth (Highest to Lowest) and take top 3
    trending_stocks = sorted(stocks_list, key=lambda x: x['change_percent'], reverse=True)[:3]

    # Close db
    conn.close()
    return render_template('dashboard.html', stocks=stocks_list, news=mock_news, trending=trending_stocks)

@app.route('/api/prices')
def get_prices():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    stocks = conn.execute("SELECT symbol, current_price, opening_price FROM stocks").fetchall()
    conn.close()
    
    stock_list = []
    for stock in stocks:
        current = stock['current_price']
        opening = stock['opening_price'] if stock['opening_price'] else current
        growth = ((current - opening) / opening * 100) if opening != 0 else 0
        
        stock_list.append({
            "symbol": stock['symbol'],
            "price": round(current, 2),
            "growth": round(growth, 2)
        })
    
    # Sort by growth (Highest to Lowest)
    sorted_stocks = sorted(stock_list, key=lambda x: x['growth'], reverse=True)
    
    return jsonify(sorted_stocks)

if __name__ == "__main__":
    init_db()

    # --- START THE THREAD ---
    # This starts the function above as a 'daemon', meaning it dies when you stop app.py
    thread = threading.Thread(target=live_price_updates, daemon=True)
    thread.start()

    app.run(debug=True)