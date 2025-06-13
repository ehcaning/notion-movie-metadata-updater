import os
from notion_client import Client
from omdb import OMDBClient
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from movie_metadata.metrics import (
    success_counter,
    failure_counter,
    processed_counter,
    fetch_gauge,
    update_duration_histogram,
)


class MovieMetadataUpdater:
    def __init__(self):
        load_dotenv()
        self.notion_db_id = os.getenv("NOTION_DB_ID")
        self.page_size = int(os.getenv("NOTION_PAGE_SIZE", 20))
        omdb_api_key = os.getenv("OMDB_API_KEY")
        notion_token = os.getenv("NOTION_TOKEN")
        self.notion = Client(auth=notion_token)
        self.omdb_client = OMDBClient(apikey=omdb_api_key)

    def update_metadata(self):
        movies = self._fetch_notion_movies()
        fetch_gauge.set(len(movies))
        for movie in tqdm(movies, desc="Processing movies"):
            imdb_id = movie["imdb_id"]
            page_id = movie["id"]
            with update_duration_histogram.time():
                try:
                    movie_data = self.omdb_client.get(imdbid=imdb_id)
                    movie_clean = {k: v for k, v in movie_data.items() if v != "N/A"}
                    tqdm.write(
                        f"Processing: {movie_clean.get('title', 'Unknown')} ({imdb_id})"
                    )
                    cover = self._get_movie_cover(movie_clean)
                    properties = self._build_properties(movie_clean)
                    if properties:
                        self.notion.pages.update(
                            page_id=page_id,
                            properties=properties,
                            icon=cover,
                        )
                    success_counter.inc()
                except Exception as e:
                    print(f"Error processing {imdb_id}: {e}")
                    failure_counter.inc()
                finally:
                    processed_counter.inc()

    def _fetch_notion_movies(self):
        db = self.notion.databases.query(
            database_id=self.notion_db_id,
            page_size=self.page_size,
            sorts=[{"property": "Updated Metadata At", "direction": "ascending"}],
        )
        results = []
        for rec in db["results"]:
            if rec["properties"]["IMDB ID"]["rich_text"]:
                imdb_id = rec["properties"]["IMDB ID"]["rich_text"][0]["text"][
                    "content"
                ]
                id = rec["id"]
                results.append({"id": id, "imdb_id": imdb_id, "raw": rec})
        return results

    def _build_properties(self, movie):
        properties = {}

        if "title" in movie and movie["title"]:
            properties["Name"] = {"title": [{"text": {"content": movie["title"]}}]}
        if "year" in movie and movie["year"]:
            try:
                properties["Year"] = {"number": float(movie["year"])}
            except Exception:
                pass
        if "imdb_votes" in movie and movie["imdb_votes"]:
            try:
                properties["IMDB Voters"] = {
                    "number": float(movie["imdb_votes"].replace(",", ""))
                }
            except Exception:
                pass
        if "director" in movie and movie["director"]:
            directors = [d.strip() for d in movie["director"].split(",") if d.strip()]
            if directors:
                properties["Director"] = {
                    "multi_select": [{"name": d} for d in directors]
                }
        if "genre" in movie and movie["genre"]:
            genres = [d.strip() for d in movie["genre"].split(",") if d.strip()]
            if genres:
                properties["Genre"] = {"multi_select": [{"name": d} for d in genres]}
        if "writer" in movie and movie["writer"]:
            writers = [d.strip() for d in movie["writer"].split(",") if d.strip()]
            if writers:
                properties["Writer"] = {"multi_select": [{"name": d} for d in writers]}
        if "actors" in movie and movie["actors"]:
            actors = [d.strip() for d in movie["actors"].split(",") if d.strip()]
            if actors:
                properties["Actors"] = {"multi_select": [{"name": d} for d in actors]}
        if "country" in movie and movie["country"]:
            countries = [d.strip() for d in movie["country"].split(",") if d.strip()]
            if countries:
                properties["Country"] = {
                    "multi_select": [{"name": d} for d in countries]
                }
        if "language" in movie and movie["language"]:
            languages = [d.strip() for d in movie["language"].split(",") if d.strip()]
            if languages:
                properties["Language"] = {
                    "multi_select": [{"name": d} for d in languages]
                }
        if "plot" in movie and movie["plot"]:
            properties["Plot"] = {"rich_text": [{"text": {"content": movie["plot"]}}]}
        if "rated" in movie and movie["rated"]:
            properties["Rated"] = {"select": {"name": movie["rated"]}}
        if "runtime" in movie and movie["runtime"]:
            try:
                properties["Runtime (m)"] = {
                    "number": float(movie["runtime"].replace(" min", ""))
                }
            except Exception:
                pass
        if "released" in movie and movie["released"]:
            try:
                properties["Released"] = {
                    "date": {
                        "start": datetime.strptime(
                            movie["released"], "%d %b %Y"
                        ).strftime("%Y-%m-%d")
                    }
                }
            except Exception:
                pass
        properties["Updated Metadata At"] = {
            "date": {
                "start": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "end": None,
            }
        }
        if movie and "ratings" in movie:
            for rating in movie["ratings"]:
                source = rating["source"]
                value = rating["value"]
                if source == "Internet Movie Database":
                    try:
                        properties["IMDB Rating"] = {
                            "number": (float(value.split("/")[0]))
                        }
                    except Exception:
                        continue
                elif source == "Rotten Tomatoes":
                    try:
                        properties[source] = {"number": float(value.replace("%", ""))}
                    except Exception:
                        continue
                elif source == "Metacritic":
                    try:
                        properties[source] = {"number": float(value.split("/")[0])}
                    except Exception:
                        continue
        return properties

    def _get_movie_cover(self, movie):
        if "poster" in movie and movie["poster"]:
            return {
                "type": "external",
                "external": {"url": movie["poster"]},
            }
        return None
