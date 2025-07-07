import uvicorn
from config import API_HTTP_PORT
from fastapi import FastAPI
from .routes import register_routes
from log_config import setup_logger


def run_server():
    logger = setup_logger(name="server_logger")
    app = FastAPI()
    register_routes(app, logger)
    uvicorn.run(app, host="0.0.0.0", port=API_HTTP_PORT, log_level="info")
