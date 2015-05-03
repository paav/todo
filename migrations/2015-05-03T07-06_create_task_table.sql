CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY NOT NULL,
    title TEXT NOT NULL, 
    body TEXT, 
    create_date INTEGER, 
    update_date INTEGER, 
    done_date INTEGER, 
    priority INTEGER
);
