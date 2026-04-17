-- 1. Wipe existing data
DELETE FROM News;
DELETE FROM stocks;

-- 2. Insert Stocks
INSERT INTO stocks (symbol, name, current_price) VALUES 
('SPACEX', 'Space Exploration Technologies Corp', 375);

-- 3. Insert News (Dynamic ID lookup)
INSERT INTO News (headline, story, stock_id, effect) VALUES 
(
  'Elon Musk buys Mars', 
  'SpaceX stock reaches the moon literally.', 
  (SELECT id FROM stocks WHERE symbol = 'SPACEX'), -- Find the ID automatically!
  700
);