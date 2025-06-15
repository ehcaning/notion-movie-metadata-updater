from prometheus_client import start_http_server
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor
from time import sleep
import os
from log_config import setup_logger

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(int(os.getenv("METRICS_HTTP_PORT", 8000)))

    sleepTime = int(os.getenv("SLEEP_TIME", 3600))
    while True:
        try:
            logger = setup_logger(name="sync_movies_logger")
            updater = MovieMetadataUpdater(logger=logger)
            extractor = TVTimeExtractor(logger=logger)
            movies = extractor.get_moveis()
            changes = TvTimeProcessor(logger=logger).get_latest_changes(movies)
            for imdb_id, data in changes.items():
                if data.get("new"):
                    logger.info(
                        "Adding new movie",
                        extra={
                            "imdb_id": imdb_id,
                            "movie": data.get("name"),
                        },
                    )
                    updater.add_movie_by_imdb_id(imdb_id, data)
                if data.get("updated"):
                    logger.info(
                        "Updating movie",
                        extra={
                            "imdb_id": imdb_id,
                            "movie": data.get("name"),
                        },
                    )
                    updater.update_movie_by_imdb_id(imdb_id, data)

        except Exception as e:
            logger.error(
                "Error in fetching movies", exc_info=True, extra={"error": str(e)}
            )
        try:
            logger = setup_logger(name="update_movies_logger")
            updater = MovieMetadataUpdater(logger=logger)
            updater.update_metadata()
        except Exception as e:
            logger.error(
                "Error in update_metadata", exc_info=True, extra={"error": str(e)}
            )

        logger.info("Sleeping", extra={"sleepTime": sleepTime})
        sleep(sleepTime)
