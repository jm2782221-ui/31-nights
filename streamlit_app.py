from datetime import date
import html
import json
import os
from pathlib import Path
import random
import tempfile

import streamlit as st
from challenge import (
    CHALLENGE_COMPLETIONS_PATH,
    CHALLENGE_NIGHTS,
    ChallengeError,
    add_challenge_completion,
    challenge_status,
    completed_nights,
    completions_for_year,
    completion_for_date,
    current_local_date,
    filter_uncompleted_recommendations,
    load_challenge_completions,
    save_challenge_completions,
)
from tmdb import enrich_movie

THEME_CSS = r"""
<style>
:root { color-scheme: dark; }
[data-testid="stAppViewContainer"] {
    color: #f2e8d8;
    background:
        radial-gradient(ellipse at 52% -12%, rgba(157, 79, 38, 0.20), transparent 44%),
        linear-gradient(180deg, #171411 0%, #100f0e 58%, #0d0d0c 100%);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }
.block-container {
    max-width: 920px;
    padding: 3rem 2.3rem 3.5rem;
}
h1, h2, h3 {
    color: #f3e8d5;
    letter-spacing: -0.025em;
}
h1 {
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(2.8rem, 6vw, 4.35rem);
    line-height: 1.06;
    margin: 0 0 0.45rem;
}
main h1::after {
    content: "";
    display: block;
    width: 3.4rem;
    height: 3px;
    margin-top: 1.05rem;
    border-radius: 99px;
    background: linear-gradient(90deg, #d47a3e, rgba(212, 122, 62, 0.18));
}
h2, h3 { font-family: Georgia, "Times New Roman", serif; }
[data-testid="stMarkdownContainer"] p {
    color: #d8cbb8;
    line-height: 1.65;
}
[data-testid="stCaptionContainer"] { color: #bbae9b; }
[data-testid="stButton"] > button {
    min-height: 2.9rem;
    padding: 0.55rem 1rem;
    border: 1px solid rgba(211, 156, 105, 0.28);
    border-radius: 12px;
    background: rgba(44, 37, 31, 0.82);
    color: #f4ead9;
    font-weight: 650;
    transition: background-color 150ms ease, border-color 150ms ease, transform 150ms ease;
}
[data-testid="stButton"] > button:hover {
    border-color: rgba(235, 155, 91, 0.72);
    background: rgba(91, 53, 32, 0.78);
    transform: translateY(-1px);
}
[data-testid="stButton"] > button[kind="primary"] {
    border-color: #c8753d;
    background: #a9562f;
    color: #fff4e4;
}
[data-testid="stButton"] > button[kind="primary"]:hover { background: #bd6837; }
[data-testid="stButton"] > button:focus-visible,
[role="combobox"]:focus-visible,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within {
    outline: 3px solid #e79a5e;
    outline-offset: 3px;
}
[data-testid="stButton"] > button:disabled {
    border-color: rgba(189, 174, 151, 0.16);
    background: rgba(39, 36, 32, 0.7);
    color: #948a7c;
    transform: none;
}
[role="combobox"] {
    min-height: 2.9rem;
    border: 1px solid rgba(211, 156, 105, 0.3);
    border-radius: 12px !important;
    background: #211e1a !important;
    color: #f4ead9 !important;
    box-shadow: none !important;
}
[role="combobox"]:hover { border-color: rgba(235, 155, 91, 0.72); }
[role="listbox"] {
    border: 1px solid rgba(211, 156, 105, 0.3);
    border-radius: 12px;
    background: #211e1a;
}
[role="option"] { color: #f2e8d8; }
[role="option"][aria-selected="true"] { background: #493023; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 2.9rem;
    border-color: rgba(211, 156, 105, 0.3);
    border-radius: 12px;
    background: #211e1a;
    color: #f4ead9;
}
[data-baseweb="popover"] [role="listbox"] {
    border: 1px solid rgba(211, 156, 105, 0.3);
    background: #211e1a;
}
[data-baseweb="popover"] [role="option"] { color: #f2e8d8; }
[data-baseweb="popover"] [role="option"]:hover { background: #493023; }
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(214, 133, 70, 0.32) !important;
    border-radius: 20px !important;
    background: linear-gradient(145deg, rgba(39, 33, 28, 0.96), rgba(26, 24, 22, 0.96));
    box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24), 0 0 32px rgba(163, 80, 37, 0.08);
    padding: 1.3rem 1.45rem;
}
hr { border-color: rgba(213, 175, 133, 0.18); }
@media (max-width: 640px) {
    .block-container { padding: 2rem 1.1rem 2.6rem; }
    h1 { font-size: 2.75rem; }
    [data-testid="stVerticalBlockBorderWrapper"] { padding: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


DATA_DIR = Path(__file__).parent / "data"
CATEGORIES = {
    "movie": ("🎬 MOVIE", "movies.json"),
    "episode": ("📺 HALLOWEEN EPISODE", "tv_episodes.json"),
    "game": ("🎮 SPOOKY GAME", "games.json"),
}
ANY_FILTER = "Any"

WATCHED_MOVIES_PATH = Path(__file__).resolve().parent / "watched_movies.json"


def movie_history_key(movie):
    normalized_title = " ".join(movie["title"].split()).casefold()
    return f"{normalized_title}::{int(movie['year'])}"


def load_watched_movies(path=WATCHED_MOVIES_PATH):
    try:
        history = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = history.get("watched", []) if isinstance(history, dict) else []
        return {
            movie_history_key(entry)
            for entry in entries
            if isinstance(entry, dict)
            and isinstance(entry.get("title"), str)
            and str(entry.get("year", "")).isdigit()
        }
    except (OSError, ValueError, TypeError):
        return set()


def save_watched_movies(watched_keys, path=WATCHED_MOVIES_PATH):
    catalog = load_recommendations(CATEGORIES["movie"][1])
    movies_by_key = {movie_history_key(movie): movie for movie in catalog}
    entries = [
        {"title": movies_by_key[key]["title"], "year": movies_by_key[key]["year"]}
        for key in sorted(watched_keys)
        if key in movies_by_key
    ]
    payload = json.dumps({"version": 1, "watched": entries}, ensure_ascii=False, indent=2)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=Path(path).parent,
            prefix=".watched_movies.", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, Path(path))
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)



def movie_roll_candidates(recommendations, watched_keys, include_watched=False):
    if include_watched:
        return list(recommendations)
    return [movie for movie in recommendations if movie_history_key(movie) not in watched_keys]


def streaming_provider_names(enrichment):
    if not isinstance(enrichment, dict):
        return []
    providers = enrichment.get("watch_providers")
    if not isinstance(providers, dict):
        return []
    raw_streaming = providers.get("streaming")
    if not isinstance(raw_streaming, list):
        return []
    return [name.strip() for name in raw_streaming if isinstance(name, str) and name.strip()]


@st.cache_data
def load_recommendations(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def days_until_halloween(today):
    halloween = date(today.year, 10, 31)

    if today > halloween:
        halloween = date(today.year + 1, 10, 31)
    return (halloween - today).days


def is_recommendation_available(recommendation, on_date=None):
    available_date = recommendation.get("available_date")
    if not available_date:
        return True
    try:
        available_on = date.fromisoformat(available_date)
    except (TypeError, ValueError):
        return False
    return available_on <= (on_date or date.today())


def coming_soon_episodes(on_date=None):
    episodes = load_recommendations(CATEGORIES["episode"][1])
    return sorted(
        [episode for episode in episodes if not is_recommendation_available(episode, on_date)],
        key=lambda episode: episode.get("available_date", ""),
    )


def recommendations_for(category, filters, on_date=None):
    _, filename = CATEGORIES[category]
    recommendations = load_recommendations(filename)

    if category == "movie":
        if filters["genre"] != ANY_FILTER:
            recommendations = [
                item for item in recommendations if item["genre"] == filters["genre"]
            ]
        if filters["scare_level"] != ANY_FILTER:
            recommendations = [
                item
                for item in recommendations
                if item["scare_level"] == filters["scare_level"]
            ]
    elif category == "episode":
        recommendations = [
            episode for episode in recommendations
            if is_recommendation_available(episode, on_date)
        ]
        if filters["show"] != ANY_FILTER:
            recommendations = [
                item for item in recommendations if item["show"] == filters["show"]
            ]
    else:
        if filters["genre"] != ANY_FILTER:
            recommendations = [
                item for item in recommendations if item["genre"] == filters["genre"]
            ]
        if filters["player_support"] != ANY_FILTER:
            player_support = filters["player_support"].lower()
            recommendations = [
                item
                for item in recommendations
                if item["player_support"] == player_support
            ]

    return recommendations


def choose_recommendation(category, filters, challenge_completions=None, today=None):
    recommendations = recommendations_for(category, filters, today)
    if challenge_completions is not None:
        recommendations = filter_uncompleted_recommendations(
            recommendations, category, challenge_completions, today
        )
    return random.choice(recommendations) if recommendations else None


@st.cache_data(ttl=21600, show_spinner=False)
def cached_movie_enrichment(title, year, access_token):
    return enrich_movie(title, year, access_token)


def filter_widget_key(category, name):
    return f"{category}_{name}_{st.session_state.filter_version}"


def show_filters(category):
    if category == "movie":
        genre_options = sorted(
            {item["genre"] for item in load_recommendations(CATEGORIES[category][1])}
        )
        genre = st.selectbox(
            "Genre",
            [ANY_FILTER, *genre_options],
            key=filter_widget_key(category, "genre"),
        )
        scare_levels = sorted(
            {
                str(item["scare_level"])
                for item in load_recommendations(CATEGORIES[category][1])
            }
        )
        scare_level = st.selectbox(
            "Scare level",
            [ANY_FILTER, *scare_levels],
            key=filter_widget_key(category, "scare_level"),
        )
        return {"genre": genre, "scare_level": int(scare_level) if scare_level != ANY_FILTER else ANY_FILTER}

    if category == "episode":
        shows = sorted(
            {item["show"] for item in load_recommendations(CATEGORIES[category][1])}
        )
        return {
            "show": st.selectbox(
                "Show",
                [ANY_FILTER, *shows],
                key=filter_widget_key(category, "show"),
            )
        }

    games = load_recommendations(CATEGORIES[category][1])
    genres = sorted({item["genre"] for item in games})
    genre = st.selectbox(
        "Genre",
        [ANY_FILTER, *genres],
        key=filter_widget_key(category, "genre"),
    )
    player_support = st.selectbox(
        "Player support",
        [ANY_FILTER, "Single-player", "Multiplayer", "Both"],
        key=filter_widget_key(category, "player_support"),
    )
    return {"genre": genre, "player_support": player_support}


def _challenge_calendar_markup(today, year_completions):
    category_labels = {"movie": "Movie", "tv": "TV Episode", "game": "Game"}
    category_icons = {"movie": "🎬", "tv": "📺", "game": "🎮"}
    completions_by_date = {record["date"]: record for record in year_completions}
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    cells = [
        f'<div class="october-day is-empty" role="presentation"></div>'
        for _ in range(date(today.year, 10, 1).weekday())
    ]

    for day in range(1, CHALLENGE_NIGHTS + 1):
        challenge_date = date(today.year, 10, day)
        date_key = challenge_date.isoformat()
        completion = completions_by_date.get(date_key)
        classes = ["october-day"]
        if completion:
            category = completion.get("category", "")
            label = category_labels.get(category, "Completion")
            icon = category_icons.get(category, "🎃")
            title = completion.get("title", "")
            marker = icon
            accessible_label = f"October {day}, completed: {label} — {title}"
            classes.append("is-completed")
            if challenge_date == today:
                classes.append("is-today")
                accessible_label = f"October {day}, today and completed: {label} — {title}"
        elif challenge_date == today:
            marker = "NOW"
            accessible_label = f"October {day}, today, not completed"
            classes.append("is-today")
        elif challenge_date > today:
            marker = "UP"
            accessible_label = f"October {day}, upcoming"
            classes.append("is-upcoming")
        else:
            marker = "—"
            accessible_label = f"October {day}, no completion"
            classes.append("is-past")

        safe_label = html.escape(accessible_label, quote=True)
        safe_title = html.escape(accessible_label, quote=True)
        cells.append(
            f'<div class="{" ".join(classes)}" role="gridcell" '
            f'aria-label="{safe_label}" title="{safe_title}">'
            f'<strong>{day}</strong><span>{marker}</span></div>'
        )

    weekday_cells = "".join(
        f'<div class="october-weekday" role="columnheader">{weekday}</div>'
        for weekday in weekdays
    )
    return (
        '<div class="october-challenge-calendar" role="grid" '
        f'aria-label="October {today.year} challenge calendar">'
        f'{weekday_cells}{"".join(cells)}</div>'
    )


def show_challenge_card(today, completions, store_path):
    status = challenge_status(today)
    year_completions = sorted(
        completions_for_year(completions, today.year), key=lambda record: record["date"]
    )
    nights = completed_nights(completions, today.year)
    percentage = round(nights * 100 / CHALLENGE_NIGHTS)
    today_completion = completion_for_date(completions, today)
    category_labels = {"movie": "Movie", "tv": "TV Episode", "game": "Game"}
    category_icons = {"movie": "🎬", "tv": "📺", "game": "🎮"}

    st.markdown(
        """<style>
        .october-challenge-calendar {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: .35rem;
            margin: .5rem 0 1rem;
        }
        .october-weekday {
            color: #c6b9a5;
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .06em;
            padding: .2rem 0;
            text-align: center;
            text-transform: uppercase;
        }
        .october-day {
            align-items: center;
            aspect-ratio: 1 / 1;
            background: rgba(255, 255, 255, .035);
            border: 1px solid rgba(255, 255, 255, .10);
            border-radius: .7rem;
            color: #eee6da;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 2.7rem;
            overflow: hidden;
        }
        .october-day strong { font-size: 1rem; line-height: 1.1; }
        .october-day span { color: #c6b9a5; font-size: .68rem; line-height: 1.2; }
        .october-day.is-empty { background: transparent; border-color: transparent; }
        .october-day.is-completed {
            background: linear-gradient(145deg, rgba(242, 139, 55, .24), rgba(109, 60, 37, .18));
            border-color: rgba(255, 166, 84, .62);
        }
        .october-day.is-completed span { color: #ffd0a2; }
        .october-day.is-today { box-shadow: inset 0 0 0 2px #ffd27d; border-color: #ffac59; }
        .october-day.is-upcoming { border-style: dashed; color: #c6b9a5; }
        .october-day.is-past { opacity: .58; }
        @media (max-width: 520px) {
            .october-challenge-calendar { gap: .18rem; }
            .october-day { border-radius: .45rem; min-height: 2.15rem; }
            .october-day strong { font-size: .86rem; }
            .october-day span, .october-weekday { font-size: .58rem; }
        }
        </style>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(f"## 🎃 October {today.year} Challenge")
        if status == "active":
            st.markdown(f"### Tonight — October {today.day}")
            if today_completion:
                category = today_completion.get("category", "")
                icon = category_icons.get(category, "🎃")
                label = category_labels.get(category, "Completion")
                st.success(
                    f"Tonight is complete: {icon} {label} — {today_completion.get('title', '')}"
                )
            else:
                category = st.session_state.get("category")
                recommendation = st.session_state.get("recommendation")
                if category in category_labels and isinstance(recommendation, dict):
                    pick_title = (
                        recommendation.get("title")
                        or recommendation.get("episode_title")
                        or recommendation.get("episode")
                        or ""
                    )
                    if category == "tv":
                        pick_title = f"{recommendation.get('show', 'TV')} — {pick_title}"
                    icon = category_icons[category]
                    label = category_labels[category]
                    st.markdown(f"**Tonight’s Pick:** {icon} {label} — {pick_title}")
                    st.caption("Use Complete Tonight below the recommendation to record the night.")
                else:
                    st.caption("Choose a category to see tonight’s pick and complete the night.")
        elif status == "upcoming":
            st.markdown(f"### Challenge opens October 1, {today.year}")
            st.caption(f"Today is {today.strftime('%B')} {today.day}.")
        elif nights == CHALLENGE_NIGHTS:
            st.success(f"All {CHALLENGE_NIGHTS} October nights are complete.")
        else:
            st.markdown(f"### October {today.year} has ended")
            st.caption(f"Final progress: {nights} of {CHALLENGE_NIGHTS} nights.")

        st.markdown(f"### {nights} / {CHALLENGE_NIGHTS} Nights Complete")
        st.progress(nights / CHALLENGE_NIGHTS)
        st.caption(f"{percentage}% complete")

        st.markdown("#### October Calendar")
        st.markdown(_challenge_calendar_markup(today, year_completions), unsafe_allow_html=True)
        st.caption("🎬 Movie  ·  📺 TV Episode  ·  🎮 Game  ·  NOW tonight  ·  UP upcoming  ·  — no completion")

        if year_completions:
            with st.expander(f"Chronological history · {len(year_completions)} completions"):
                for record in year_completions:
                    completed_date = date.fromisoformat(record["date"])
                    category = record.get("category", "")
                    icon = category_icons.get(category, "🎃")
                    label = category_labels.get(category, "Completion")
                    st.write(f"Oct {completed_date.day} — {icon} {label} — {record.get('title', '')}")
        else:
            st.caption("No dated completions recorded for this October.")

        if st.session_state.confirm_challenge_reset:
            st.warning(
                "Reset Challenge removes only the dated V1.8 challenge completion records. "
                "It does NOT remove your separate V1.7 watched-movie history."
            )
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm challenge reset", key="confirm_challenge_reset_button", use_container_width=True):
                    save_challenge_completions([], store_path)
                    st.session_state.confirm_challenge_reset = False
                    st.rerun()
            with cancel_col:
                if st.button("Cancel reset", key="cancel_challenge_reset"):
                    st.session_state.confirm_challenge_reset = False
                    st.rerun()
        elif st.button("Reset Challenge", key="start_challenge_reset"):
            st.session_state.confirm_challenge_reset = True
            st.rerun()

        st.caption(
            "Reset Challenge clears only the dated challenge completion records. "
            "It never removes the separate V1.7 watched-movie history."
        )


    st.caption("Public demo history is shared across visitors and may not persist between restarts.")

def show_recommendation(category, recommendation, enrichment=None):
    if category == "movie":
        st.subheader(recommendation["title"])
        st.caption(
            f'{recommendation["year"]} · {recommendation["genre"]} · '
            f'Scare level {recommendation["scare_level"]}/5'
        )

        if enrichment:
            poster_col, details_col = st.columns([1, 3])
            with poster_col:
                if enrichment.get("poster_url"):
                    st.image(enrichment["poster_url"], use_container_width=True)

            with details_col:
                if enrichment.get("overview"):
                    st.write(enrichment["overview"])

                metadata = []
                if enrichment.get("release_date"):
                    metadata.append(f'Released {enrichment["release_date"]}')

                runtime = enrichment.get("runtime")
                if isinstance(runtime, int) and not isinstance(runtime, bool) and runtime > 0:
                    hours, minutes = divmod(runtime, 60)
                    runtime_label = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                    metadata.append(f"Runtime: {runtime_label}")

                rating = enrichment.get("rating")
                if isinstance(rating, (int, float)) and not isinstance(rating, bool):
                    metadata.append(f"TMDB Rating: {rating:.1f}/10")

                if metadata:
                    st.caption(" · ".join(metadata))

                streaming = streaming_provider_names(enrichment)
                if streaming:
                    st.caption("Available on in the U.S.")
                    for name in streaming:
                        st.text(f"- {name}")
                else:
                    st.caption("No U.S. streaming providers are listed for this movie.")
                st.caption("Availability data by JustWatch via TMDB; listings can change.")

        st.caption("Movie details provided by TMDB. Not endorsed or certified by TMDB.")
    elif category == "episode":
        st.subheader(
            f'{recommendation["show"]}: {recommendation["episode_title"]}'
        )
        if recommendation.get("season") is None or recommendation.get("episode_number") is None:
            special_year = recommendation.get("special_year")
            special_label = f"{special_year} Halloween special" if special_year else "Halloween special"
            available_date = recommendation.get("available_date")
            if available_date:
                special_label += f" · Available {available_date}"
            st.caption(special_label)
        else:
            st.caption(
                f'Season {recommendation["season"]} · '
                f'Episode {recommendation["episode_number"]}'
            )
    else:
        st.subheader(recommendation["title"])
        st.caption(
            f'{recommendation["genre"]} · '
            f'{recommendation["player_support"].replace("_", " ").title()}'
        )

test_today = st.session_state.get("_challenge_test_today")
browser_timezone = getattr(st.context, "timezone", None)
today = current_local_date(test_today, browser_timezone)
st.title("31 Nights 🎃")
st.subheader(f"{days_until_halloween(today)} days until Halloween!")
st.write("What do you want to roll?")

if "category" not in st.session_state:
    st.session_state.category = None
if "recommendation" not in st.session_state:
    st.session_state.recommendation = None
if "filters" not in st.session_state:
    st.session_state.filters = {}
if "filter_version" not in st.session_state:
    st.session_state.filter_version = 0
if "recommendation_date" not in st.session_state:
    st.session_state.recommendation_date = None
if "confirm_challenge_reset" not in st.session_state:
    st.session_state.confirm_challenge_reset = False


test_challenge_path = st.session_state.get("_challenge_test_store_path")
challenge_store_path = (
    Path(test_challenge_path)
    if isinstance(test_challenge_path, str) and test_challenge_path
    else CHALLENGE_COMPLETIONS_PATH
)
test_watched_path = st.session_state.get("_challenge_test_watched_path")
watched_history_path = (
    Path(test_watched_path)
    if isinstance(test_watched_path, str) and test_watched_path
    else WATCHED_MOVIES_PATH
)
challenge_completions = load_challenge_completions(challenge_store_path)
if st.session_state.recommendation_date != today.isoformat():
    st.session_state.recommendation = None
    st.session_state.recommendation_date = today.isoformat()
    st.session_state.marked_movie_key = None

col1, col2, col3 = st.columns(3)
for column, category in zip((col1, col2, col3), CATEGORIES):
    with column:
        if st.button(CATEGORIES[category][0], use_container_width=True):
            st.session_state.category = category
            st.session_state.recommendation = None
            st.session_state.filters = {}
            st.session_state.filter_version += 1

coming_soon = coming_soon_episodes(today)
if coming_soon:
    st.subheader("Coming Soon")
    for episode in coming_soon:
        st.write(
            f"{episode['show']}: {episode['episode_title']} · "
            f"Available {episode.get('available_date', 'Date not set')}"
        )


show_challenge_card(today, challenge_completions, challenge_store_path)

if st.session_state.category is not None:
    category = st.session_state.category
    filters = show_filters(category)
    st.session_state.filters = filters
    all_matches = recommendations_for(category, filters, today)
    matches = all_matches
    watched_keys = set()
    include_watched = False

    if category == "movie":
        watched_keys = load_watched_movies(watched_history_path)
        include_watched = st.checkbox(
            "Include watched movies in future rolls",
            key=filter_widget_key(category, "include_watched"),
        )
        with st.expander(f"Watched movies ({len(watched_keys)})"):
            watched_titles = sorted(
                (
                    movie for movie in load_recommendations(CATEGORIES["movie"][1])
                    if movie_history_key(movie) in watched_keys
                ),
                key=lambda movie: (movie["title"].casefold(), movie["year"]),
            )
            if watched_titles:
                for movie in watched_titles:
                    st.write(f"{movie['title']} ({movie['year']})")
                if st.button("Clear watched history", key="clear_watched_history"):
                    save_watched_movies(set(), watched_history_path)
                    st.session_state.marked_movie_key = None
                    st.rerun()
            else:
                st.caption("No movies marked as watched yet.")
        matches = movie_roll_candidates(all_matches, watched_keys, include_watched)

    matches_before_challenge = matches
    matches = filter_uncompleted_recommendations(
        matches, category, challenge_completions, today
    )
    no_uncompleted_challenge_matches = (
        challenge_status(today) == "active"
        and completion_for_date(challenge_completions, today) is None
        and bool(matches_before_challenge)
        and not matches
    )

    current = st.session_state.recommendation
    preserve_marked_movie = (
        category == "movie" and current is not None
        and movie_history_key(current) == st.session_state.get("marked_movie_key")
        and current in all_matches
    )
    if not preserve_marked_movie and current not in matches:
        st.session_state.recommendation = random.choice(matches) if matches else None

    recommendation = st.session_state.recommendation
    all_matching_movies_watched = (
        category == "movie" and bool(all_matches) and not matches_before_challenge and not include_watched
    )
    if all_matching_movies_watched:
        st.info(
            "Every movie matching these filters is already marked as watched. "
            "Include watched movies or clear watched history to roll again."
        )
    if recommendation is None:
        if all_matching_movies_watched:
            st.info(
                "Every movie matching these filters is already marked as watched. "
                "Include watched movies or clear watched history to roll again."
            )
        elif no_uncompleted_challenge_matches:
            st.info(
                "Every recommendation matching these filters is already completed in this October challenge. "
                "Try another category or filter."
            )
        else:
            st.info("No recommendations match those filters. Try another combination.")
    else:
        enrichment = None
        if category == "movie":
            enrichment = cached_movie_enrichment(
                recommendation["title"], recommendation["year"],
                os.getenv("TMDB_READ_ACCESS_TOKEN", ""),
            )
        st.subheader(
            "Tonight’s Pick"
            if challenge_status(today) == "active" and completion_for_date(challenge_completions, today) is None
            else "Recommendation"
        )
        with st.container(border=True):
            show_recommendation(category, recommendation, enrichment)
        if category == "movie":
            current_key = movie_history_key(recommendation)
            if current_key in watched_keys:
                st.caption("Already watched · future movie rolls skip this title by default.")
            elif st.button("Mark as Watched", key=f"mark_watched_{st.session_state.filter_version}"):
                watched_keys.add(current_key)
                save_watched_movies(watched_keys, watched_history_path)
                st.session_state.marked_movie_key = current_key
                st.rerun()

    if challenge_status(today) == "active":
        if completion_for_date(challenge_completions, today):
            st.caption("Tonight is already complete. You can keep browsing, but a second completion cannot be added for this date.")
        elif st.button("Complete Tonight", key=f"complete_tonight_{today.isoformat()}", type="primary"):
            try:
                updated_completions = add_challenge_completion(
                    challenge_completions, category, recommendation, today
                )
                save_challenge_completions(updated_completions, challenge_store_path)
            except ChallengeError as error:
                st.error(str(error))
            else:
                st.rerun()

    roll_col, change_col = st.columns(2)
    with roll_col:
        if st.button("🎲 Roll Again", disabled=not matches, use_container_width=True):
            st.session_state.recommendation = random.choice(matches)
            st.session_state.recommendation_date = today.isoformat()
            st.session_state.marked_movie_key = None
            st.rerun()
    with change_col:
        if st.button("🔄 Choose Something Else", use_container_width=True):
            st.session_state.category = None
            st.session_state.recommendation = None
            st.session_state.filters = {}
            st.session_state.filter_version += 1
            st.session_state.marked_movie_key = None
