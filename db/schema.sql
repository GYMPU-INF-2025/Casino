CREATE TABLE IF NOT EXISTS users (
    id bigserial PRIMARY KEY NOT NULL,
    username text NOT NULL,
    password text NOT NULL,
    money integer DEFAULT 0 NOT NULL
)