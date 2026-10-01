import json
import http.client
import math
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher


API_ROOT = "https://api.themoviedb.org/3"
IMAGE_ROOT = "https://image.tmdb.org/t/p/w342"
MATCH_THRESHOLD = 0.85


def _request_json(path, params, access_token):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{API_ROOT}{path}?{query}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or payload.get("success") is False:
        raise ValueError("Invalid TMDB response")
    return payload


def _normalized_title(title):
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_title.casefold())


def _close_title_score(curated_title, result):
    curated = _normalized_title(curated_title)
    candidates = [result.get("title"), result.get("original_title")]
    return max(
        (
            SequenceMatcher(None, curated, _normalized_title(candidate)).ratio()
            for candidate in candidates
            if isinstance(candidate, str) and candidate.strip()
        ),
        default=0,
    )


def _release_year(result):
    release_date = result.get("release_date")
    if not isinstance(release_date, str) or len(release_date) < 4:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


def _available_details(result):
    details = {}
    overview = result.get("overview")
    if isinstance(overview, str) and overview.strip():
        details["overview"] = overview.strip()

    release_date = result.get("release_date")
    if isinstance(release_date, str) and release_date.strip():
        details["release_date"] = release_date
        details["year"] = _release_year(result)

    poster_path = result.get("poster_path")
    if isinstance(poster_path, str) and poster_path.startswith("/"):
        details["poster_url"] = f"{IMAGE_ROOT}{poster_path}"

    rating = result.get("vote_average")
    if isinstance(rating, (int, float)) and not isinstance(rating, bool):
        if math.isfinite(rating) and rating > 0:
            details["rating"] = rating

    runtime = result.get("runtime")
    if isinstance(runtime, int) and not isinstance(runtime, bool) and runtime > 0:
        details["runtime"] = runtime
    return details


def _watch_provider_details(payload):
    if not isinstance(payload, dict):
        return None

    regions = payload.get("results")
    if not isinstance(regions, dict):
        return None
    us = regions.get("US")
    if not isinstance(us, dict):
        return {}

    def provider_names(category):
        entries = us.get(category)
        if not isinstance(entries, list):
            return []
        names = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("provider_name")
            if isinstance(name, str):
                name = name.strip()
                if name and name not in names:
                    names.append(name)
        return names

    details = {
        "streaming": [],
        "rent": provider_names("rent"),
        "buy": provider_names("buy"),
    }
    for category in ("flatrate", "free", "ads"):
        for name in provider_names(category):
            if name not in details["streaming"]:
                details["streaming"].append(name)

    link = us.get("link")
    if isinstance(link, str):
        try:
            parsed_link = urllib.parse.urlparse(link)
        except ValueError:
            parsed_link = None
        if (
            parsed_link is not None
            and parsed_link.scheme == "https"
            and parsed_link.netloc.lower() == "www.themoviedb.org"
        ):
            details["link"] = link
    return details


def _get_tmdb_access_token(access_token=None, streamlit_secrets=None):
    if access_token:
        return access_token
    env_token = os.getenv("TMDB_READ_ACCESS_TOKEN")
    if env_token:
        return env_token
    if streamlit_secrets is None:
        try:
            import streamlit as st

            streamlit_secrets = st.secrets
        except Exception:
            return None
    try:
        return streamlit_secrets.get("TMDB_READ_ACCESS_TOKEN") or None
    except Exception:
        return None


def enrich_movie(title, year, access_token=None):
    """Return validated TMDB metadata, or None when enrichment is unavailable."""
    access_token = _get_tmdb_access_token(access_token)
    if not access_token or not isinstance(title, str) or not title.strip():
        return None

    try:
        search = _request_json(
            "/search/movie",
            {"query": title, "year": year, "include_adult": "false"},
            access_token,
        )
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        OSError,
        ValueError,
        TypeError,
    ):
        return None

    results = search.get("results")
    if not isinstance(results, list):
        return None

    matches = [
        result
        for result in results
        if isinstance(result, dict)
        and _release_year(result) == year
        and _close_title_score(title, result) >= MATCH_THRESHOLD
    ]
    if not matches:
        return None

    match = max(matches, key=lambda result: _close_title_score(title, result))
    movie_details = _available_details(match)
    movie_id = match.get("id")
    if "runtime" not in movie_details and type(movie_id) is int and movie_id > 0:
        try:
            extra = _request_json(f"/movie/{movie_id}", {}, access_token)
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            TimeoutError,
            OSError,
            ValueError,
            TypeError,
        ):

            extra = None
        if isinstance(extra, dict) and extra.get("id") == movie_id:
            runtime = _available_details(extra).get("runtime")
            if runtime is not None:
                movie_details["runtime"] = runtime

    if type(movie_id) is int and movie_id > 0:
        try:
            provider_response = _request_json(
                f"/movie/{movie_id}/watch/providers", {}, access_token
            )
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            TimeoutError,
            OSError,
            ValueError,
            TypeError,
        ):
            provider_response = None
        watch_providers = _watch_provider_details(provider_response)
        if watch_providers is not None:
            movie_details["watch_providers"] = watch_providers

    return movie_details
