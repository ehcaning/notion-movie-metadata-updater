import prometheus_client
from movie_metadata import MovieMetadataUpdater
from tvtime_extractor import TvTimeProcessor, TVTimeExtractor
from time import sleep
import threading
from log_config import setup_logger
from server import run_server
from config import SLEEP_TIME, METRICS_HTTP_PORT, TVTIME_SYNC_DISABLED, METADATA_UPDATER_DISABLED


class TvTimeSync:
    def __init__(self):
        self.disabled = TVTIME_SYNC_DISABLED
        self.logger = setup_logger(name="sync_movies_logger")

    def sync(self):
        if self.disabled:
            self.logger.info("TVTime sync is disabled, skipping TVTime movie sync")
            return

        try:
            updater = MovieMetadataUpdater(logger=self.logger)
            extractor = TVTimeExtractor(logger=self.logger)
            movies = extractor.get_movies()
            changes = TvTimeProcessor(logger=self.logger).get_latest_changes(movies)
            if not changes:
                self.logger.info("No new changes found in TVTime data")
                return

            for imdb_id, data in changes.items():
                updater.upsert_movie_by_imdb_id(imdb_id, data)
                updater.update_movie_metadata_by_imdb_id(imdb_id)

        except Exception as e:
            self.logger.error(
                "Error in fetching movies",
                exc_info=True,
                extra={"error": str(e)},
            )


class MetadataUpdater:
    def __init__(self):
        self.disabled = METADATA_UPDATER_DISABLED
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
                "Error in update_metadata",
                exc_info=True,
                extra={"error": str(e)},
            )


if __name__ == "__main__":
    logger = setup_logger(name="main_logger")

    prometheus_client.start_http_server(METRICS_HTTP_PORT)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    tvtime_sync = TvTimeSync()
    metadata_updater = MetadataUpdater()
    while True:
        tvtime_sync.sync()
        metadata_updater.update()

        logger.info("Sleeping", extra={"sleepTime": SLEEP_TIME})
        sleep(SLEEP_TIME)
