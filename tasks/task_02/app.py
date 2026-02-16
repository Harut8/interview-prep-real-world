import sqlite3
import jwt
from flask import Flask, request, jsonify, g

app = Flask(__name__)
SECRET_KEY = "super-secret-key"
DATABASE = "users.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
    )
    db.commit()


def get_user_by_username(username: str) -> dict | None:
    db = get_db()
    # BUG: SQL injection vulnerability
    cursor = db.execute(
        f"SELECT * FROM users WHERE username = '{username}'"
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "User already exists"}), 409

    db = get_db()
    # BUG: Storing plain-text password
    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password),
    )
    db.commit()
    return jsonify({"message": "User created"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # BUG: Plain-text comparison, no hashing
    if user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    # BUG: Token never expires
    token = jwt.encode(
        {"user_id": user["id"], "username": username},
        SECRET_KEY,
        algorithm="HS256",
    )
    return jsonify({"token": token})


@app.route("/protected", methods=["GET"])
def protected():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    return jsonify({"message": f"Hello, {payload['username']}!"})


# TODO: Add POST /refresh endpoint


with app.app_context():
    init_db()
