import requests
from requests.exceptions import RequestException, HTTPError
from config import TVTIME_USERNAME, TVTIME_PASSWORD
from logging import Logger

# non-sensitive information
USER_AGENT = "TVTime for iOS 8.44.0-202208302674-prod"
APP_VERSION = "202208302674"
X_API_Key = "LhqxB7GE9a95beFHqiNC85GHdrX8hNi34H2uQ7QG"
# non-sensitive information


class TVTimeExtractor:
    def __init__(self, logger: Logger):
        self.username: str = TVTIME_USERNAME
        self.password: str = TVTIME_PASSWORD
        self.logger: Logger = logger

    def get_movies(self):
        """Fetch tracked movies for the configured user.

        Raises:
            requests.exceptions.RequestException on network errors,
            requests.exceptions.HTTPError for 4xx/5xx responses,
            ValueError if response JSON is invalid.
        """
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

        try:
            response = requests.get(url, headers=headers, timeout=10)
        except RequestException:
            self.logger.error("Network error while fetching movies", exc_info=True)
            raise

        # Handle HTTP error status codes explicitly so we can log details
        if 400 <= response.status_code <= 499:
            self.logger.error(
                "Client error fetching movies",
                extra={"status_code": response.status_code, "response_text": response.text},
                exc_info=True,
            )
            raise HTTPError("Client error fetching movies", response=response)
        if 500 <= response.status_code <= 599:
            self.logger.error(
                "Server error fetching movies",
                extra={"status_code": response.status_code, "response_text": response.text},
                exc_info=True,
            )
            raise HTTPError("Server error fetching movies", response=response)

        try:
            json_response = response.json()
        except ValueError:
            self.logger.error("Invalid JSON response when fetching movies", exc_info=True)
            raise

        return json_response

    def _login(self):
        """Perform login and return (tvst_access_token, user_id).

        Raises the same exceptions as `get_movies` for network and HTTP errors,
        and KeyError if the expected fields are missing from the JSON.
        """
        url = "https://api2.tozelabs.com/v2/signin"

        payload = {
            "username": self.username,
            "password": self.password,
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
        except RequestException:
            self.logger.error("Network error during TVTime login", exc_info=True)
            raise

        if 400 <= response.status_code <= 499:
            self.logger.error(
                "Client error during TVTime login",
                extra={"status_code": response.status_code, "response_text": response.text},
                exc_info=True,
            )
            raise HTTPError("Client error during TVTime login", response=response)
        if 500 <= response.status_code <= 599:
            self.logger.error(
                "Server error during TVTime login",
                extra={"status_code": response.status_code, "response_text": response.text},
                exc_info=True,
            )
            raise HTTPError("Server error during TVTime login", response=response)

        try:
            json_response = response.json()
        except ValueError:
            self.logger.error("Invalid JSON during TVTime login", exc_info=True)
            raise

        try:
            return json_response["tvst_access_token"], json_response["id"]
        except KeyError:
            self.logger.error(
                "Missing expected login fields in response", extra={"response_json": json_response}, exc_info=True
            )
            raise KeyError("Missing expected login fields in response")
