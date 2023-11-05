-- Create the file table if it doesn't exist
CREATE TABLE IF NOT EXISTS file (
    name VARCHAR(255) PRIMARY KEY,
    type VARCHAR(255) NOT NULL,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);


CREATE TABLE IF NOT EXISTS tag (
    file_name VARCHAR(255) REFERENCES file(name) ON DELETE CASCADE,
    tag_key VARCHAR(255),
    tag_value VARCHAR(255),
    PRIMARY KEY (file_name, tag_key, tag_value)
);
