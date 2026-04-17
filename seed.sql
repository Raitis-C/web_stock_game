-- -- 1. Wipe existing data (Optional, but keeps things clean during testing)
-- DELETE FROM stocks;
-- DELETE FROM News;


-- -- 2. Insert funny News stories
-- INSERT INTO News (headline, story, stock_id, effect) VALUES 
-- ('Elon Musk buys Mars', 'SpaceX stock reaches the moon literally.', 1, +700),
-- -- ('Apple releases iToaster', 'Bread prices expected to rise 200%.', 2),
-- -- ('AI Gains Sentience, Buys Only Pizza', 'The latest trading algorithm has stopped buying stocks and spent the entire corporate treasury on 4.5 million pepperoni pizzas.', 2),
-- -- ('Bitcoin becomes official currency of Atlantis', 'Submarine sales are up.', 3);


-- -- 3. Insert Starting Stocks
-- INSERT INTO stocks (symbol, name, current_price) VALUES 
-- ('SPACEX', 'Space Exploration Technologies Corporation', 375)