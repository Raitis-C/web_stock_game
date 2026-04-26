-- 1. Wipe existing data
DELETE FROM News;
DELETE FROM stocks;

-- 2. Insert Stocks
INSERT INTO stocks (symbol, name, initial_price, volatility) VALUES 
('SPACEX', 'Space Exploration Technologies Corp', 375, 5),
('BTC', 'Bitcoin', 90000, 500),
('WEAT', 'Wheat', 600, 1),
('CL', 'Crude Oil WTI', 94, 3)

-- 3. Insert News (Dynamic ID lookup)
INSERT INTO News (headline, story, stock_id, effect) VALUES 
(
  'Elon Musk buys Mars', 
  'SpaceX stock reaches the moon literally.', 
  (SELECT id FROM stocks WHERE symbol = 'SPACEX'), -- Find the ID automatically!
  700
);


-- Set current_price and opening_price to initial_price ONLY if they are currently NULL
UPDATE stocks 
SET current_price = initial_price 
WHERE current_price IS NULL;

UPDATE stocks 
SET opening_price = initial_price 
WHERE opening_price IS NULL;