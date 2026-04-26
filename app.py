from pathlib import Path
import sqlite3
import random
import time
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)
DB_PATH = Path("stock_game_db")

def init_db():
    # Modern check using pathlib
    if not DB_PATH.exists():
        print(f"🚀 {DB_PATH} not found. Building database...")
        connection = sqlite3.connect(DB_PATH)
        
        # Using Path to read text is much cleaner
        schema_file = Path("Scripts/schema.sql")
        seed_file = Path("Scripts/seed.sql")
        
        if schema_file.exists():
            connection.executescript(schema_file.read_text())
            
        if seed_file.exists():
            connection.executescript(seed_file.read_text())
            
        connection.commit()
        connection.close()
        print("✅ Database created and seeded!")
    
    else:
        print(f"🚀 {DB_PATH} already there!")

def live_update_prices():
    """This function runs in the background forever, updating prices."""
    print("💓 Price heartbeat started...")
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
            print(f"❌ Heartbeat Error: {e}")

        # 5. Wait for 5 seconds
        time.sleep(5)

# --- START THE THREAD ---
# This starts the function above as a 'daemon', meaning it dies when you stop app.py
thread = threading.Thread(target=live_update_prices, daemon=True)
thread.start()

@app.route('/')
def index():
    # Connect to the DB path object (sqlite3 accepts Path objects)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Fetch stock and news data from db
    # stocks = conn.execute("SELECT * FROM stocks").fetchall()
    # news = conn.execute("SELECT * FROM News ORDER BY RANDOM() LIMIT 1").fetchone()

    mock_stocks = [
        {'symbol': 'BTC', 'change': 2.54},
        {'symbol': 'APPL', 'change': -1.15},
        {'symbol': 'TSLA', 'change': 0.85}
    ]
    
    mock_news = [
        {'headline': 'Apple releases iToster, bread price skyrockets', 'impact': 5.2},
        {'headline': 'CEO of popular tech company admits he just guesses what buttons do', 'impact': -8.4},
        {'headline': 'Scientists discover new color, patent pending', 'impact': 1.1}
    ]

    # Close db
    conn.close()
    return render_template('dashboard.html', stocks=mock_stocks, news=mock_news)

@app.route('/api/prices')
def get_prices():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    stocks = conn.execute("SELECT symbol, current_price FROM stocks").fetchall()
    conn.close()
    
    # Convert the database rows into a simple dictionary { "SPACEX": 375.21, ... }
    return jsonify({stock['symbol']: stock['current_price'] for stock in stocks})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)