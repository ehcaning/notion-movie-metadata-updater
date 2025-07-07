from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from .auth import get_token
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor
from http import HTTPStatus


def register_routes(app, logger):
    @app.post("/update-metadata")
    async def update_metadata_endpoint(request: Request, token: str = Depends(get_token)):
        body = await request.json()
        try:
            imdb_id = body["data"]["properties"]["IMDB ID"]["rich_text"][0]["plain_text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.warning("Invalid request body structure", extra={"error": str(e)})
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid request body structure")
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
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to update metadata")

    @app.post("/update-list")
    async def update_list_endpoint(request: Request, token: str = Depends(get_token)):
        try:
            updater = MovieMetadataUpdater(logger=logger)
            extractor = TVTimeExtractor(logger=logger)
            movies = extractor.get_movies()
            changes = TvTimeProcessor(logger=logger).get_latest_changes(movies)
            for imdb_id, data in changes.items():
                updater.upsert_movie_by_imdb_id(imdb_id, data)
                updater.update_movie_metadata_by_imdb_id(imdb_id)

            logger.info(f"Successfully updated movies list")
            return JSONResponse({"status": "success"})
        except Exception as e:
            logger.error(
                "API error in update_movie_by_imdb_id",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to update list")
