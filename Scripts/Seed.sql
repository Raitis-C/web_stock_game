-- 1. Insert Stocks
INSERT OR IGNORE INTO stocks (symbol, name, initial_price, volatility) VALUES
('SPACEX', 'Space Exploration Technologies Corp', 375, 5),
('BTC', 'Bitcoin', 90000, 500),
('WEAT', 'Wheat', 600, 1),
('CL', 'Crude Oil WTI', 94, 3);

-- 2. Insert News (Dynamic ID lookup)
INSERT OR IGNORE INTO News (headline, stock_id, effect) VALUES 
('Elon Musk buys Mars, SpaceX stock reaches moon literally', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 700),
('Apple releases iToster, bread price skyrockets', (SELECT id FROM stocks WHERE symbol = 'WEAT'), 450),
('CEO of popular tech company admits he just guesses what buttons do', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), -250),
('Scientists discorver new color, patent pending', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 75),
('AI Gains Sentience, Buys Only Pizza', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 75),
('Bitcoin becomes official currency of Atlantis, submarine sales are up', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 75);


-- 3. Set current_price and opening_price to initial_price ONLY if they are currently NULL
UPDATE stocks 
SET current_price = initial_price 
WHERE current_price IS NULL;

UPDATE stocks 
SET opening_price = initial_price 
WHERE opening_price IS NULL;