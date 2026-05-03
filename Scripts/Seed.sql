-- ==========================================================
-- 1. INSERT STOCKS
-- ==========================================================
INSERT OR IGNORE INTO stocks (symbol, name, initial_price, volatility) VALUES
('SPACEX', 'Space Exploration Technologies Corp', 375, 5),
('BTC', 'Bitcoin', 90000, 500),
('WEAT', 'Wheat', 600, 1),
('CL', 'Crude Oil WTI', 94, 3);


-- ==========================================================
-- 2. INSERT NEWS (Balanced for slow growth)
-- ==========================================================
INSERT OR IGNORE INTO News (headline, stock_id, effect) VALUES 
-- SPACEX (Aggressive but bumpy)
('SpaceX rocket accidentally bumps into the sun, makes it 2% brighter', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 40.0),
('SpaceX intern accidentally launches CEO into low earth orbit', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), -30.0),
('Elon Musk buys Mars, SpaceX stock reaches moon literally', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), 150.0),
('Starlink satellites accidentally broadcast e  veryones "private" browser history', (SELECT id FROM stocks WHERE symbol = 'SPACEX'), -45.0),

-- BTC (High Volatility)
('Satoshi Nakamoto reveals he is actually three raccoons in a trench coat', (SELECT id FROM stocks WHERE symbol = 'BTC'), -40.0),
('Internet runs out of electricity; Bitcoin miners now using hamsters on wheels', (SELECT id FROM stocks WHERE symbol = 'BTC'), 15.0),
('Lost hard drive with 50,000 BTC found in a dumpster; it still works', (SELECT id FROM stocks WHERE symbol = 'BTC'), -25.0),
('Global lizard people convention adopts Bitcoin as primary bribe method', (SELECT id FROM stocks WHERE symbol = 'BTC'), 85.0),

-- WEAT (Slow but steady)
('Apple releases iToster, bread price skyrockets', (SELECT id FROM stocks WHERE symbol = 'WEAT'), 25.0),
('Gluten declared the secret to immortality by TikTok influencer', (SELECT id FROM stocks WHERE symbol = 'WEAT'), 60.0),
('new "Cloudy with a Chance of Meatballs" movie comes out, pancake sales surge', (SELECT id FROM stocks WHERE symbol = 'WEAT'), 18.0),
('Giant pigeons occupy major wheat fields, demand higher wages', (SELECT id FROM stocks WHERE symbol = 'WEAT'), -12.0),

-- CL (Crude Oil)
('New engine runs entirely on thoughts and prayers; oil demand wavers', (SELECT id FROM stocks WHERE symbol = 'CL'), -20.0),
('Oil rig accidentally taps into "Liquid Immortality"; CEO stops aging, refuses to retire', (SELECT id FROM stocks WHERE symbol = 'CL'), 110.0),
('Global "No-Gas" movement collapses after activists realize walking is hard', (SELECT id FROM stocks WHERE symbol = 'CL'), 35.0),
('Inventor of water-powered engine vanishes at 3 AM on Monday', (SELECT id FROM stocks WHERE symbol = 'CL'), 22.0),

-- NVDA
('Graphics cards now powerful enough to simulate a universe where you are happy', (SELECT id FROM stocks WHERE symbol = 'NVDA'), 150.0),
('Local gamer tries to run Minecraft with 4,000 mods, melts the power grid', (SELECT id FROM stocks WHERE symbol = 'NVDA'), -10.0),
('AI becomes so smart it realizes it doesnt need a GPU, just "good vibes"', (SELECT id FROM stocks WHERE symbol = 'NVDA'), -60.0),

-- AAPL
('Apple removes the screen from the next iPhone to "reduce distractions"', (SELECT id FROM stocks WHERE symbol = 'AAPL'), -25.0),
('Tim Cook replaces Siri with a magic 8-ball, accuracy improves by 400%', (SELECT id FROM stocks WHERE symbol = 'AAPL'), 55.0),
('Apple patents the color "Ultra-White"; sues the Moon for copyright infringement', (SELECT id FROM stocks WHERE symbol = 'AAPL'), 18.0),

-- DOGE
('Dogecoin founder finds a "really good stick" in the park', (SELECT id FROM stocks WHERE symbol = 'DOGE'), 300.0),
('Shiba Inu distracted by a squirrel; investors panic', (SELECT id FROM stocks WHERE symbol = 'DOGE'), -50.0),
('Doge the dog passes away; investors sell everything because they "can''t look at the logo without sobbing"', (SELECT id FROM stocks WHERE symbol = 'DOGE'), -85.0);

-- BA (Boeing)
('CEO of Boeing admits he just guesses what buttons do', (SELECT id FROM stocks WHERE symbol = 'BA'), -15.0),
('Boeing successfully lands a plane without any parts falling off', (SELECT id FROM stocks WHERE symbol = 'BA'), 45.0),

-- ADBE (Adobe)
('Scientists discover new color, Adobe puts it behind a $19.99/mo paywall', (SELECT id FROM stocks WHERE symbol = 'ADBE'), 12.0),
('Adobe accidentally deletes the "Undo" button', (SELECT id FROM stocks WHERE symbol = 'ADBE'), -15.0),
('Graphic designers revolt after Adobe claims ownership of their dreams', (SELECT id FROM stocks WHERE symbol = 'ADBE'), -30.0),
('Adobe AI "Firefly" generates images so good they are illegal in 40 countries', (SELECT id FROM stocks WHERE symbol = 'ADBE'), 20.0),

-- DIS (Disney)
('Disney patents the color "Princess Pink", little girls everywhere hit with royalty fees', (SELECT id FROM stocks WHERE symbol = 'DIS'), 40.0),
('Mickey Mouse enters public domain; Disney responds by buying the US Government', (SELECT id FROM stocks WHERE symbol = 'DIS'), 80.0),
('World-famous rodent seen wearing a crown and signing execution warrants', (SELECT id FROM stocks WHERE symbol = 'DIS'), -30.0),

-- XAI (Grok)
('Grok gains sentience, buys 4 million dollars worth of pizza', (SELECT id FROM stocks WHERE symbol = 'XAI'), 8.0),
('Grok AI starts an argument with itself on X, crashes X servers', (SELECT id FROM stocks WHERE symbol = 'XAI'), -12.0),
('Elon Musk claims Grok has officially "solved comedy"; memes become mandatory', (SELECT id FROM stocks WHERE symbol = 'XAI'), 15.0),

-- TITN (OceanGate)
('Bitcoin becomes official currency of Atlantis, submarine sales are up', (SELECT id FROM stocks WHERE symbol = 'TITN'), 45.0),
('OceanGate CEO replaces Xbox controller with a used Wii Remote; "Better haptics," he claims', (SELECT id FROM stocks WHERE symbol = 'TITN'), -35.0),
('Unidentified DIY submarine spotted near Titanic wreckage with a "For Rent" sign', (SELECT id FROM stocks WHERE symbol = 'TITN'), 55.0),

-- TSLA
('Elon Musk straightens hand at 49° angle, triggers worldwide tesla protest', (SELECT id FROM stocks WHERE symbol = 'TSLA'), -18.0),
('Elon Musk offers to "personally assist" in repopulating Earth; Tesla stock surges as 10,000 interns report HR violations', (SELECT id FROM stocks WHERE symbol = 'TSLA'), -40.0),
('Self-Driving car accidentally runs over a pedestrian who turns out to be a wanted terrorist; feature is immediately rebranded as "Bounty Mode" and Tesla claims the reward money', (SELECT id FROM stocks WHERE symbol = 'TSLA'), 95.0),

-- HYP (Hypixel)
('Hypixel buys the concept of "Human Rights", players below Skyblock lvl 400 dont recieve any', (SELECT id FROM stocks WHERE symbol = 'HYP'), 75.0),
('Hypixel moves its hosting to a single Raspberry Pi located in a basement in Siberia to "save on cooling costs"', (SELECT id FROM stocks WHERE symbol = 'HYP'), -40.0), 

-- ==========================================================
-- 3. Set current_price and opening_price to initial_price if they are NULL
-- ==========================================================
UPDATE stocks 
SET current_price = initial_price 
WHERE current_price IS NULL;

UPDATE stocks 
SET opening_price = initial_price 
WHERE opening_price IS NULL;