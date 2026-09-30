"""Local, dated completion history for the October 31 Nights challenge."""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json
import os
from pathlib import Path
import tempfile

CHALLENGE_COMPLETIONS_PATH = Path(__file__).resolve().parent / "challenge_completions.json"
CHALLENGE_MONTH = 10
CHALLENGE_NIGHTS = 31
VALID_CATEGORIES = {"movie", "tv", "game"}


class ChallengeError(ValueError):
    """Base error for a challenge completion that cannot be recorded."""


class ChallengeInactiveError(ChallengeError):
    """Raised when a completion is attempted outside October."""


class ChallengeDateAlreadyCompleteError(ChallengeError):
    """Raised when a second completion is attempted for one local date."""


class ChallengeRecommendationAlreadyCompleteError(ChallengeError):
    """Raised when an item already completed in this October is repeated."""


def current_local_date(override=None, timezone_name=None, now=None):
    """Return the user's local date, or an explicit date supplied by a test."""
    if type(override) is date:
        return override
    try:
        zone = ZoneInfo(timezone_name) if timezone_name else None
    except (ZoneInfoNotFoundError, ValueError):
        zone = None
    if now is not None:
        if zone is not None and now.tzinfo is not None:
            return now.astimezone(zone).date()
        return now.date()
    return datetime.now(zone).date() if zone is not None else date.today()


def challenge_status(today=None):
    today = current_local_date(today)
    if today.month < CHALLENGE_MONTH:
        return "upcoming"
    if today.month > CHALLENGE_MONTH:
        return "completed"
    return "active"


def challenge_day(today=None):
    today = current_local_date(today)
    return today.day if today.month == CHALLENGE_MONTH else None


def _category_key(category):
    return "tv" if category == "episode" else category


def _normalized(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Recommendation identity fields must be non-empty text.")
    return " ".join(value.split()).casefold()


def recommendation_identity(category, recommendation):
    """Build a stable identity that distinguishes movies, episodes, and games."""
    category = _category_key(category)
    if category == "movie":
        try:
            year = int(recommendation["year"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Movies need a title and year for a stable identity.") from None
        parts = [category, _normalized(recommendation.get("title")), year]
    elif category == "tv":
        parts = [
            category,
            _normalized(recommendation.get("show")),
            _normalized(recommendation.get("episode_title")),
        ]
        season = recommendation.get("season")
        episode_number = recommendation.get("episode_number")
        if season is not None or episode_number is not None:
            parts.extend([season, episode_number])
    elif category == "game":
        parts = [category, _normalized(recommendation.get("title"))]
    else:
        raise ValueError(f"Unsupported challenge category: {category}")
    return json.dumps(parts, ensure_ascii=False, separators=(",", ":"))


def recommendation_title(category, recommendation):
    category = _category_key(category)
    if category == "movie":
        return f"{recommendation['title']} ({recommendation['year']})"
    if category == "tv":
        title = f"{recommendation['show']}: {recommendation['episode_title']}"
        season = recommendation.get("season")
        episode_number = recommendation.get("episode_number")
        if season is not None and episode_number is not None:
            title += f" (S{season} E{episode_number})"
        return title
    if category == "game":
        return recommendation["title"]
    raise ValueError(f"Unsupported challenge category: {category}")


def _valid_record(record):
    if not isinstance(record, dict):
        return None
    date_text = record.get("date")
    category = record.get("category")
    identity = record.get("identity")
    title = record.get("title")
    if not all(isinstance(value, str) and value.strip() for value in (date_text, identity, title)):
        return None
    if category not in VALID_CATEGORIES:
        return None
    try:
        parsed_date = date.fromisoformat(date_text)
    except ValueError:
        return None
    if parsed_date.isoformat() != date_text or parsed_date.month != CHALLENGE_MONTH:
        return None
    return {"date": date_text, "category": category, "identity": identity, "title": title}


def _sort_records(records):
    return sorted(records, key=lambda record: (record["date"], record["category"], record["title"].casefold()))


def load_challenge_completions(path=CHALLENGE_COMPLETIONS_PATH):
    """Load valid October records; this file is separate from watched_movies.json."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    entries = payload.get("completions", []) if isinstance(payload, dict) else []
    if not isinstance(entries, list):
        return []

    valid = []
    seen_dates = set()
    seen_year_identities = set()
    for raw_record in entries:
        record = _valid_record(raw_record)
        if record is None:
            continue
        parsed_date = date.fromisoformat(record["date"])
        year_identity = (parsed_date.year, record["identity"])
        if record["date"] in seen_dates or year_identity in seen_year_identities:
            continue
        valid.append(record)
        seen_dates.add(record["date"])
        seen_year_identities.add(year_identity)
    return _sort_records(valid)


def save_challenge_completions(completions, path=CHALLENGE_COMPLETIONS_PATH):
    """Atomically save challenge records without touching movie watch history."""
    records = []
    seen_dates = set()
    seen_year_identities = set()
    for raw_record in completions:
        record = _valid_record(raw_record)
        if record is None:
            raise ValueError("Challenge records must have an October date, category, identity, and title.")
        parsed_date = date.fromisoformat(record["date"])
        year_identity = (parsed_date.year, record["identity"])
        if record["date"] in seen_dates:
            raise ChallengeDateAlreadyCompleteError("Only one challenge completion is allowed per local date.")
        if year_identity in seen_year_identities:
            raise ChallengeRecommendationAlreadyCompleteError("A challenge recommendation can be completed only once per October.")
        records.append(record)
        seen_dates.add(record["date"])
        seen_year_identities.add(year_identity)

    payload = json.dumps({"version": 1, "completions": _sort_records(records)}, ensure_ascii=False, indent=2)
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".challenge_completions.", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def completions_for_year(completions, year):
    return [record for record in completions if record["date"].startswith(f"{year:04d}-10-")]


def completion_for_date(completions, today=None):
    date_text = current_local_date(today).isoformat()
    return next((record for record in completions if record["date"] == date_text), None)


def completed_nights(completions, year):
    return min(len({record["date"] for record in completions_for_year(completions, year)}), CHALLENGE_NIGHTS)


def filter_uncompleted_recommendations(recommendations, category, completions, today=None):
    """Skip prior challenge picks only while a new October completion is available."""
    today = current_local_date(today)
    if challenge_status(today) != "active" or completion_for_date(completions, today):
        return list(recommendations)
    completed_ids = {
        record["identity"]
        for record in completions_for_year(completions, today.year)
    }
    return [
        recommendation
        for recommendation in recommendations
        if recommendation_identity(category, recommendation) not in completed_ids
    ]


def add_challenge_completion(completions, category, recommendation, today=None):
    today = current_local_date(today)
    if challenge_status(today) != "active":
        raise ChallengeInactiveError("The October challenge accepts completions only during October.")
    if completion_for_date(completions, today):
        raise ChallengeDateAlreadyCompleteError("Tonight already has a challenge completion.")
    identity = recommendation_identity(category, recommendation)
    if any(
        record["identity"] == identity
        for record in completions_for_year(completions, today.year)
    ):
        raise ChallengeRecommendationAlreadyCompleteError("This recommendation was already completed during the October challenge.")

    record = {
        "date": today.isoformat(),
        "category": _category_key(category),
        "identity": identity,
        "title": recommendation_title(category, recommendation),
    }
    return _sort_records([*completions, record])
