
DROP TABLE IF EXISTS brewery_temps;
CREATE TABLE brewery_temps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brew_run TEXT NOT NULL,
  temps array NOT NULL,
  date_time TEXT NOT NULL
);