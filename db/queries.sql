-- name: GetUserById :one
SELECT * FROM users WHERE users.id = ?;

-- name: GetUserByUsername :one
SELECT * FROM users WHERE users.username = ?;
