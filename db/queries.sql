-- name: GetUserById :one
SELECT * FROM users WHERE users.id = ?;