from pathlib import Path
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
DB_PATH = Path("stock_game_db") # No extension, just like your "ghost" file!

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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)