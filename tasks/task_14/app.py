import random
import time
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# In-memory session storage
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def generate_session_id() -> str:
    """Generate a session ID."""
    # BUG: not cryptographically secure
    return str(random.randint(100000, 999999))


def create_session(user_id: str, username: str) -> str:
    """Create a new session for a user."""
    session_id = generate_session_id()
    sessions[session_id] = {
        "user_id": user_id,
        "username": username,
        "created_at": time.time(),
        # BUG: no expiration
    }
    return session_id


def get_session(session_id: str) -> dict | None:
    """Get a session by ID."""
    return sessions.get(session_id)


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
        return True
    return False


def get_all_sessions_for_user(user_id: str) -> list[dict]:
    """Get all sessions for a specific user."""
    # BUG: O(n) scan over all sessions — needs secondary index
    result = []
    for sid, session in sessions.items():
        if session["user_id"] == user_id:
            result.append({"session_id": sid, **session})
    return result


# Simulated user database
USERS = {
    "alice": {"id": "1", "password": "password123"},
    "bob": {"id": "2", "password": "bobpass"},
}


@app.post("/login")
def login(request: LoginRequest, response: Response):
    user = USERS.get(request.username)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = create_session(user["id"], request.username)
    response.set_cookie("session_id", session_id)
    return {"message": "Logged in", "session_id": session_id}


@app.get("/me")
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session(session_id)
    # BUG: if cookie exists but session was deleted, returns 500 (NoneType error below)
    return {"username": session["username"], "user_id": session["user_id"]}


@app.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out"}


# TODO: Add session expiration with sliding TTL
# TODO: Add DELETE /sessions to invalidate all user sessions
# TODO: Add session metadata (user agent, IP, timestamps)
