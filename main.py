from prometheus_client import start_http_server
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor
from time import sleep
import os
from log_config import setup_logger
from server import run_server
import threading
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    sleepTime = int(os.getenv("SLEEP_TIME", 3600))

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    start_http_server(int(os.getenv("METRICS_HTTP_PORT", 8000)))

    while True:
        try:
            logger = setup_logger(name="sync_movies_logger")
            updater = MovieMetadataUpdater(logger=logger)
            extractor = TVTimeExtractor(logger=logger)
            movies = extractor.get_moveis()
            changes = TvTimeProcessor(logger=logger).get_latest_changes(movies)
            for imdb_id, data in changes.items():
                if data.get("new"):
                    updater.add_movie_by_imdb_id(imdb_id, data)
                if data.get("updated"):
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
