import json


class TvTimeProcessor:
    def __init__(self, json_file="tvtime_state.json"):
        self.json_file = json_file

    def _get_previous_state(self):
        try:
            with open(self.json_file, "r") as file:
                return json.load(file)
        except:
            print(f"Could not read previous state from {self.json_file}")
            return {}

    def _save_current_state(self, converted_data):
        with open(self.json_file, "w") as file:
            json.dump(converted_data, file, indent=2)

    def _convert(self, json_data):
        result = {}
        for obj in json_data.get("data", {}).get("objects", []):
            imdb_id = obj.get("meta", {}).get("imdb_id")
            if not imdb_id:
                continue

            result[imdb_id] = {
                "name": obj.get("meta", {}).get("name"),
                "rewatch_count": obj.get("rewatch_count", 0),
                "watched_at": obj.get("watched_at", None),
            }
        return result

    def get_latest_changes(self, json_data):
        changes = {}
        current_state = self._convert(json_data)
        previous_state = self._get_previous_state()
        if not previous_state:
            self._save_current_state(current_state)
            return {}

        for imdb_id, current_info in current_state.items():
            previous_info = previous_state.get(imdb_id, None)
            if not previous_info:
                changes[imdb_id] = {
                    "name": current_info.get("name"),
                    "watched_at": current_info.get("watched_at"),
                    "rewatch_count": current_info.get("rewatch_count"),
                    "new": True,
                }
            elif current_info.get("watched_at") != previous_info.get(
                "watched_at"
            ) or current_info.get("rewatch_count") != previous_info.get(
                "rewatch_count"
            ):
                changes[imdb_id] = {
                    "name": current_info.get("name"),
                    "watched_at": current_info.get("watched_at"),
                    "rewatch_count": current_info.get("rewatch_count"),
                    "updated": True,
                }

        self._save_current_state(current_state)
        return changes
