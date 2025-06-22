import prometheus_client
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor
from time import sleep
import os
from log_config import setup_logger
from server import run_server
import threading
from dotenv import load_dotenv


class TvtimeSync:
    def __init__(self):
        self.disabled = os.getenv("TVTIME_SYNC_DISABLED", "false").lower() == "true"
        self.logger = setup_logger(name="sync_movies_logger")

    def sync(self):
        if self.disabled:
            self.logger.info("TVTime sync is disabled, skipping TVTime movie sync")
            return

        try:
            updater = MovieMetadataUpdater(logger=self.logger)
            extractor = TVTimeExtractor(logger=self.logger)
            movies = extractor.get_moveis()
            changes = TvTimeProcessor(logger=self.logger).get_latest_changes(movies)
            if not changes:
                self.logger.info("No new changes found in TVTime data")
                return

            for imdb_id, data in changes.items():
                updater.upsert_movie_by_imdb_id(imdb_id, data)
                updater.update_movie_metadata_by_imdb_id(imdb_id)

        except Exception as e:
            self.logger.error(
                "Error in fetching movies", exc_info=True, extra={"error": str(e)}
            )


class MetadataUpdater:
    def __init__(self):
        self.disabled = (
            os.getenv("METADATA_UPDATER_DISABLED", "false").lower() == "true"
        )
        self.logger = setup_logger(name="update_movies_logger")

    def update(self):
        if self.disabled:
            self.logger.info("Metadata updater is disabled, skipping metadata update")
            return

        try:
            updater = MovieMetadataUpdater(logger=self.logger)
            updater.bulk_update_movie_metadata()
        except Exception as e:
            self.logger.error(
                "Error in update_metadata", exc_info=True, extra={"error": str(e)}
            )


if __name__ == "__main__":
    load_dotenv()
    sleepTime = int(os.getenv("SLEEP_TIME", 3600))
    logger = setup_logger(name="main_logger")

    prometheus_client.start_http_server(int(os.getenv("METRICS_HTTP_PORT", 8000)))
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    tvtime_sync = TvtimeSync()
    metadata_updater = MetadataUpdater()
    while True:
        tvtime_sync.sync()
        metadata_updater.update()

        logger.info("Sleeping", extra={"sleepTime": sleepTime})
        sleep(sleepTime)
