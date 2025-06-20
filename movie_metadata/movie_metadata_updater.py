import os
from notion_client import Client
from omdb import OMDBClient
from datetime import datetime
from movie_metadata.metrics import (
    success_counter,
    failure_counter,
    processed_counter,
    fetch_gauge,
    update_duration_histogram,
)


class MovieMetadataUpdater:
    def __init__(self, logger=None):
        self.notion_db_id = os.getenv("NOTION_DB_ID")
        self.page_size = int(os.getenv("NOTION_PAGE_SIZE", 20))
        omdb_api_key = os.getenv("OMDB_API_KEY")
        notion_token = os.getenv("NOTION_TOKEN")
        self.notion = Client(auth=notion_token)
        self.omdb_client = OMDBClient(apikey=omdb_api_key)
        self.logger = logger

    def bulk_update_movie_metadata(self):
        notion_movie_records = self._fetch_notion_movies()
        fetch_gauge.set(len(notion_movie_records))
        for notion_movie_record in notion_movie_records:
            imdb_id = notion_movie_record.get("imdb_id")
            self.update_movie_metadata_by_imdb_id(imdb_id)

    def update_movie_metadata_by_imdb_id(self, imdb_id):
        with update_duration_histogram.time():
            try:

                notion_page_id = self._get_notion_page_id_by_imdb_id(imdb_id)
                if not notion_page_id:
                    raise ValueError(f"No Notion page found for IMDB ID: {imdb_id}")

                movie_data = self._get_movie_data(imdb_id)
                properties = self._build_properties(movie_data)

                if not properties:
                    raise ValueError(
                        f"No properties to update movie metadata, IMDB ID: {imdb_id}"
                    )

                self.logger.info(
                    "Updating movie metadata",
                    extra={
                        "title": movie_data.get("title", "Unknown"),
                        "imdb_id": imdb_id,
                    },
                )
                self.notion.pages.update(
                    page_id=notion_page_id,
                    properties=properties,
                    icon=self._get_movie_cover(movie_data),
                )
                success_counter.inc()
            except Exception as e:
                self.logger.error(
                    "Error updating movie metadata",
                    exc_info=True,
                    extra={"imdb_id": imdb_id, "error": str(e)},
                )
                failure_counter.inc()
            finally:
                processed_counter.inc()

    def upsert_movie_by_imdb_id(self, imdb_id, details):
        try:
            self.logger.info(
                "Upserting movie",
                extra={"imdb_id": imdb_id, "details": details},
            )

            notion_page_id = self._get_notion_page_id_by_imdb_id(imdb_id)
            if not notion_page_id:
                self.logger.debug(f"Creating movie with IMDB ID: {imdb_id}")
                self.notion.pages.create(
                    parent={"database_id": self.notion_db_id},
                    properties={
                        "IMDB ID": {"rich_text": [{"text": {"content": imdb_id}}]}
                    },
                )

            properties = {}
            watched_at = details.get("watched_at", None)
            rewatch_count = details.get("rewatch_count", 0)
            if watched_at:
                properties["Watch Date"] = {"date": {"start": watched_at}}
                properties["Watch Count"] = {"number": rewatch_count + 1}

            if not properties:
                raise ValueError(
                    "No properties to upsert movie, IMDB ID: {}".format(imdb_id)
                )

            self.notion.pages.update(
                page_id=notion_page_id,
                properties=properties,
            )
        except Exception as e:
            self.logger.error(
                "Error upserting movie by IMDB ID",
                exc_info=True,
                extra={"imdb_id": imdb_id, "details": details, "error": str(e)},
            )

    def _fetch_notion_movies(self):
        db = self.notion.databases.query(
            database_id=self.notion_db_id,
            page_size=self.page_size,
            sorts=[{"property": "Updated Metadata At", "direction": "ascending"}],
        )
        results = []
        for rec in db["results"]:
            if not rec["properties"]["IMDB ID"]["rich_text"]:
                self.logger.warning(
                    "No IMDB ID found for Notion record",
                    extra={"properties": rec["properties"]},
                )
                continue

            imdb_id = rec["properties"]["IMDB ID"]["rich_text"][0]["text"]["content"]
            id = rec["id"]
            results.append({"id": id, "imdb_id": imdb_id, "raw": rec})
        return results

    def _build_properties(self, movie):
        properties = {}

        if "imdb_id" in movie and movie["imdb_id"]:
            properties["IMDB ID"] = {
                "rich_text": [{"text": {"content": movie["imdb_id"]}}]
            }
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

    def _get_notion_page_id_by_imdb_id(self, imdb_id):
        db = self.notion.databases.query(
            database_id=self.notion_db_id,
            filter={"property": "IMDB ID", "rich_text": {"equals": imdb_id}},
        )
        if len(db["results"]) == 0:
            self.logger.error(f"No record found in database for {imdb_id}")
            return None
        if len(db["results"]) != 1:
            self.logger.error(
                f"More than 1 record in database for {imdb_id}, picking first"
            )
        return db["results"][0]["id"]

    def _get_movie_data(self, imdb_id):
        movie_data = self.omdb_client.get(imdbid=imdb_id)
        return {k: v for k, v in movie_data.items() if v != "N/A"}
