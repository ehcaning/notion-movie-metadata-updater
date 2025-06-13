from prometheus_client import start_http_server
from movie_metadata import MovieMetadataUpdater
from time import sleep
import os
from log_config import setup_logger

if __name__ == "__main__":
    logger = setup_logger()
    # Start Prometheus metrics server
    start_http_server(int(os.getenv("METRICS_HTTP_PORT", 8000)))

    updater = MovieMetadataUpdater(logger=logger)
    sleepTime = int(os.getenv("SLEEP_TIME", 3600))
    while True:
        try:
            updater.update_metadata()
        except Exception as e:
            logger.error(
                "Error in update_metadata", exc_info=True, extra={"error": str(e)}
            )
        logger.info("Sleeping", extra={"sleepTime": sleepTime})
        sleep(sleepTime)
