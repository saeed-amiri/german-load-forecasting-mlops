-- sql/auth/user.sql

CREATE SEQUENCE IF NOT EXISTS user_id_seq START 1;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY DEFAULT nextval('user_id_seq'),
    username VARCHAR UNIQUE NOT NULL,
    password_hashed VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'user'
);