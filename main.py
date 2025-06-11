from movie_metadata import MovieMetadataUpdater
from time import sleep
import os

if __name__ == "__main__":
    updater = MovieMetadataUpdater()
    sleepTime = int(os.getenv("SLEEP_TIME", 3600))
    while True:
        try:
            updater.update_metadata()
        except Exception as e:
            print(f"Error: {e}")
        print(f"Sleeping for {sleepTime} seconds...")
        sleep(sleepTime)
