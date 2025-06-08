-- name: GetUserById :one
SELECT *
FROM users
WHERE users.id = ?;

-- name: GetUserByUsername :one
SELECT *
FROM users
WHERE users.username = ?;

-- name: CreateUser :execrows
INSERT INTO users(id, username, password, money)
VALUES (?, ?, ?, ?)