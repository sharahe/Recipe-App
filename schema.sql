CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    room TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER,
    name TEXT,
    category TEXT,
    quantity FLOAT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_name TEXT,
    cuisine TEXT,
    serving_size INTEGER,
    prep_time INTEGER,
    cook_time INTEGER,
    total_time INTEGER,
    instructions TEXT,
    additional_notes TEXT,
    img_str_file TEXT,
    deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS recipe_to_ingredients (
    recipe_id INTEGER,
    ingredient_id INTEGER,
    quantity FLOAT,
    unit TEXT
);

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INTEGER,
    ingredient_name TEXT,
    ingredient_category TEXT
);