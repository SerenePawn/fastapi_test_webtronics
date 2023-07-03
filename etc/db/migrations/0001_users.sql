-- migrate:up


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    en BOOLEAN DEFAULT TRUE,
    name VARCHAR(250),
    email VARCHAR(250),
    password VARCHAR(250),
    ctime TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() at time zone 'utc'),
    atime TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    dtime TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL
);

CREATE UNIQUE INDEX users_email on users(email);
CREATE INDEX users_name_email on users(name, email);


-- migrate:down


DROP TABLE users CASCADE;
