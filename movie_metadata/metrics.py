from prometheus_client import Counter

success_counter = Counter(
    "movie_metadata_update_success_total",
    "Number of successful movie metadata updates",
)
failure_counter = Counter(
    "movie_metadata_update_failure_total",
    "Number of failed movie metadata updates",
)
