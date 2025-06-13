from prometheus_client import start_http_server
from movie_metadata import MovieMetadataUpdater
from time import sleep
import os

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(int(os.getenv("METRICS_HTTP_PORT", 8000)))

    updater = MovieMetadataUpdater()
    sleepTime = int(os.getenv("SLEEP_TIME", 3600))
    while True:
        try:
            updater.update_metadata()
        except Exception as e:
            print(f"Error: {e}")
        print(f"Sleeping for {sleepTime} seconds...")
        sleep(sleepTime)
