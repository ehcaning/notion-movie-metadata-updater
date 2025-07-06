import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
NOTION_PAGE_SIZE = int(os.getenv("NOTION_PAGE_SIZE", 20))

# OMDB
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# TVTime
TVTIME_USERNAME = os.getenv("TVTIME_USERNAME")
TVTIME_PASSWORD = os.getenv("TVTIME_PASSWORD")
TVTIME_SYNC_DISABLED = os.getenv("TVTIME_SYNC_DISABLED", "false").lower() == "true"

# API
API_TOKEN = os.getenv("API_TOKEN")
API_HTTP_PORT = int(os.getenv("API_HTTP_PORT", 8001))

# Metrics
METRICS_HTTP_PORT = int(os.getenv("METRICS_HTTP_PORT", 8000))

# General
SLEEP_TIME = int(os.getenv("SLEEP_TIME", 3600))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
METADATA_UPDATER_DISABLED = os.getenv("METADATA_UPDATER_DISABLED", "false").lower() == "true"

# Timezone
TZ = os.getenv("TZ", "Europe/Berlin")
