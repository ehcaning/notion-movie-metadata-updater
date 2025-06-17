from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import uvicorn
import os
from log_config import setup_logger
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor

# Create a custom logger for the server
logger = setup_logger(name="server_logger")

API_HTTP_PORT = int(os.getenv("API_HTTP_PORT", 8001))


def create_app():
    API_TOKEN = os.getenv("API_TOKEN")
    app = FastAPI()

    def get_token(request: Request):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            raise HTTPException(
                status_code=401, detail="Missing or invalid Authorization header"
            )
        token = auth.split(" ", 1)[1]
        if token != API_TOKEN:
            logger.warning("Invalid token provided")
            raise HTTPException(status_code=403, detail="Invalid token")
        return token

    @app.post("/update-metadata")
    async def update_metadata_endpoint(
        request: Request, token: str = Depends(get_token)
    ):
        body = await request.json()
        try:
            imdb_id = body["data"]["properties"]["IMDB ID"]["rich_text"][0][
                "plain_text"
            ]

        except (KeyError, IndexError, TypeError) as e:
            logger.warning("Invalid request body structure", extra={"error": str(e)})
            raise HTTPException(
                status_code=400, detail="Invalid request body structure"
            )
        updater = MovieMetadataUpdater(logger=logger)
        try:
            updater.update_movie_metadata_by_imdb_id(imdb_id)
            logger.info(f"Successfully updated metadata for imdb_id={imdb_id}")
            return JSONResponse({"status": "success", "imdb_id": imdb_id})
        except Exception as e:
            logger.error(
                "API error in update_movie_by_imdb_id",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise HTTPException(status_code=500, detail="Failed to update metadata")

    @app.post("/update-list")
    async def update_list_endpoint(request: Request, token: str = Depends(get_token)):
        try:
            updater = MovieMetadataUpdater(logger=logger)
            extractor = TVTimeExtractor(logger=logger)
            movies = extractor.get_moveis()
            changes = TvTimeProcessor(logger=logger).get_latest_changes(movies)
            for imdb_id, data in changes.items():
                if data.get("new"):
                    updater.add_movie_by_imdb_id(imdb_id, data)
                if data.get("updated"):
                    updater.update_movie_by_imdb_id(imdb_id, data)

            logger.info(f"Successfully updated movies list")
            return JSONResponse({"status": "success"})
        except Exception as e:
            logger.error(
                "API error in update_movie_by_imdb_id",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise HTTPException(status_code=500, detail="Failed to update list")

    return app


def run_server():
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=API_HTTP_PORT, log_level="info")
