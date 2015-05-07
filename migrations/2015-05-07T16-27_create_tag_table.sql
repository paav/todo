CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL, 
    task_id INTEGER NOT NULL,
    CONSTRAINT fk_task$tag FOREIGN KEY(task_id) REFERENCES task(id)
);

CREATE INDEX ix_fk_task$tag ON tag(task_id);
