CREATE TABLE IF NOT EXISTS teststand_steps (
  step_id TEXT PRIMARY KEY,
  name TEXT,
  description TEXT,
  parameters_json TEXT
);

CREATE TABLE IF NOT EXISTS labview_vis (
  vi_id TEXT PRIMARY KEY,
  name TEXT,
  path TEXT,
  description TEXT,
  parameters_json TEXT
);
