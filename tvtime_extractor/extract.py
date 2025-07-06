import requests
from config import TVTIME_USERNAME, TVTIME_PASSWORD

# non-sensitive information
USER_AGENT = "TVTime for iOS 8.44.0-202208302674-prod"
APP_VERSION = "202208302674"
X_API_Key = "LhqxB7GE9a95beFHqiNC85GHdrX8hNi34H2uQ7QG"
# non-sensitive information


class TVTimeExtractor:
    def __init__(self, logger=None):
        self.username = TVTIME_USERNAME
        self.password = TVTIME_PASSWORD
        self.logger = logger

    def get_movies(self):
        tvst_access_token, user_id = self._login()
        url = f"https://msapi.tvtime.com/prod/v1/tracking/cgw/follows/user/{user_id}?app_version=8.44.0&entity_type=movie&sort=watched_date,desc"
        headers = {
            "Authorization": f"Bearer {tvst_access_token}",
            "User-Agent": USER_AGENT,
            "X-API-Key": X_API_Key,
            "app-version": APP_VERSION,
            "country-code": "en",
            "user-lang-setting": "en",
        }

        response = requests.get(url, headers=headers)
        json_response = response.json()

        return json_response

    def _login(self):
        url = "https://api2.tozelabs.com/v2/signin"

        payload = {
            "username": self.username,
            "password": self.password,
        }
        response = requests.post(url, data=payload)
        json_response = response.json()

        return json_response["tvst_access_token"], json_response["id"]
