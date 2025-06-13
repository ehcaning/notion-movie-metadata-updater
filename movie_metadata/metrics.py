from prometheus_client import Counter, Histogram, Gauge

success_counter = Counter(
    "movie_metadata_update_success_total",
    "Number of successful movie metadata updates",
)
failure_counter = Counter(
    "movie_metadata_update_failure_total",
    "Number of failed movie metadata updates",
)
processed_counter = Counter(
    "movie_metadata_processed_total",
    "Total number of movies processed (success + failure)",
)
fetch_gauge = Gauge(
    "movie_metadata_notion_movies_fetched",
    "Number of movies fetched from Notion database",
)
update_duration_histogram = Histogram(
    "movie_metadata_update_duration_seconds",
    "Time spent updating a single movie's metadata",
)
