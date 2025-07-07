from fastapi import Request, HTTPException, Depends
from log_config import setup_logger
from config import API_TOKEN
from http import HTTPStatus

logger = setup_logger(name="auth_logger")


def get_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1]
    if token != API_TOKEN:
        logger.warning("Invalid token provided")
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid token")
    return token
