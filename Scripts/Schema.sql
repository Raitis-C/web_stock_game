-- stocks definition

CREATE TABLE stocks (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	symbol TEXT NOT NULL,
	name TEXT NOT NULL,
	initial_price REAL NOT NULL,
	current_price REAL,
	opening_price REAL,
	volatility REAL NOT NULL
);


-- users definition

CREATE TABLE users (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL,
	password TEXT NOT NULL,
	balance REAL DEFAULT (10000) NOT NULL
);


-- News definition

CREATE TABLE News (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	headline TEXT NOT NULL,
	stock_id INTEGER NOT NULL,
	effect REAL NOT NULL,
	CONSTRAINT News_stocks_FK FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE ON UPDATE CASCADE
);


-- portfolio definition

CREATE TABLE portfolio (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER,
	stock_id INTEGER,
	quantity REAL NOT NULL,
	CONSTRAINT portfolio_users_FK FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT portfolio_stocks_FK FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE ON UPDATE CASCADE
);


-- price_history definition

CREATE TABLE price_history (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	stock_id INTEGER,
	price REAL NOT NULL,
	"timestamp" DATETIME DEFAULT (CURRENT_TIMESTAMP),
	CONSTRAINT price_history_stocks_FK FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE ON UPDATE CASCADE
);


-- Tracks which news events have actually been triggered by the server
CREATE TABLE news_events (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL,
    triggered_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT news_events_news_FK FOREIGN KEY (news_id) REFERENCES News(id) ON DELETE CASCADE
);	