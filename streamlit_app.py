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
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');
:root {
    color-scheme: dark;
    --crypt: #170c14;
    --velvet: #2a1322;
    --velvet-deep: #1f0e1a;
    --gilt: #c8a35a;
    --gilt-bright: #e6c983;
    --gilt-faint: rgba(200, 163, 90, 0.28);
    --candle: #f1e4c6;
    --ash: #a6968a;
    --blood: #7a1e22;
    --display: "Cinzel", "Trajan Pro", Georgia, serif;
    --body: "EB Garamond", Garamond, Georgia, serif;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: var(--crypt);
}
[data-testid="stAppViewContainer"] {
    color: var(--candle);
    background:
        radial-gradient(ellipse 70% 40% at 50% 0%, rgba(122, 30, 34, 0.30), transparent 70%),
        radial-gradient(ellipse 50% 30% at 50% 100%, rgba(42, 19, 34, 0.9), transparent 80%),
        var(--crypt);
}
[data-testid="stHeader"] { background: transparent; }
.block-container {
    max-width: 860px;
    padding: 3.5rem 2rem 4rem;
}
html, body, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"], button, input, [role="combobox"], [role="option"],
[data-testid="stExpander"] summary {
    font-family: var(--body) !important;
}
[data-testid="stMarkdownContainer"] p, [data-testid="stText"] {
    color: #e2d4b8;
    font-size: 1.12rem;
    line-height: 1.6;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: var(--ash);
    font-size: 1rem;
}
h1, h2, h3, h4 {
    font-family: var(--display) !important;
    color: var(--candle);
    font-weight: 600;
    letter-spacing: 0.04em;
}
h2 { font-size: 1.55rem; }
h3 { font-size: 1.2rem; }
h4 { font-size: 1rem; color: var(--gilt); }

/* Title plaque */
h1 {
    font-size: clamp(2.9rem, 8vw, 4.6rem) !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    text-align: center;
    letter-spacing: 0.08em;
    color: var(--candle);
    text-shadow: 0 0 28px rgba(200, 163, 90, 0.18);
    padding-bottom: 0.2rem !important;
}
h1 a, h2 a, h3 a { display: none !important; }
.st-key-hero { text-align: center; gap: 0.3rem; margin-bottom: 0.6rem; }
.st-key-hero h3 {
    font-family: var(--body) !important;
    font-style: italic;
    font-weight: 400;
    font-size: 1.35rem;
    letter-spacing: 0.01em;
    color: var(--gilt);
    text-align: center;
}
.st-key-hero [data-testid="stMarkdownContainer"] p { text-align: center; color: var(--ash); }
.gilt-rule {
    display: flex; align-items: center; gap: 0.9rem;
    margin: 1rem auto 0.4rem; max-width: 22rem; color: var(--gilt);
}
.gilt-rule::before, .gilt-rule::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gilt));
}
.gilt-rule::after { background: linear-gradient(90deg, var(--gilt), transparent); }
.gilt-rule span { font-size: 0.8rem; line-height: 1; }

/* Buttons */
[data-testid="stButton"] button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
    min-height: 3rem;
    padding: 0.55rem 1.1rem;
    border: 1px solid var(--gilt-faint);
    border-radius: 2px;
    background: rgba(42, 19, 34, 0.55);
    color: var(--candle);
    font-size: 1.08rem;
    letter-spacing: 0.02em;
    transition: border-color 160ms ease, background-color 160ms ease, color 160ms ease;
}
[data-testid="stButton"] button:hover {
    border-color: var(--gilt);
    background: rgba(58, 24, 44, 0.85);
    color: var(--gilt-bright);
}
[data-testid="stButton"] button[kind="primary"], [data-testid="stBaseButton-primary"] {
    border-color: var(--gilt);
    background: linear-gradient(180deg, #d9b86f, #b08843);
    font-weight: 600;
}
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"]:hover p {
    color: #1d0f17 !important;
    font-weight: 600;
    font-size: 1.12rem;
    letter-spacing: 0.03em;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(180deg, #e6c983, #c39c52);
}
[data-testid="stButton"] button:disabled {
    border-color: rgba(166, 150, 138, 0.18);
    background: transparent;
    color: #6f6259;
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stCheckbox"] label:focus-within,
[data-baseweb="select"]:focus-within {
    outline: 2px solid var(--gilt-bright) !important;
    outline-offset: 3px;
}
.st-key-category_row [data-testid="stButton"] button {
    min-height: 3.6rem;
}
.st-key-category_row [data-testid="stButton"] button p {
    font-family: var(--display) !important;
    font-size: 0.92rem;
    letter-spacing: 0.04em;
    white-space: normal;
    line-height: 1.25;
}

/* Selects and checkbox (Streamlit 1.64 uses react-aria markup) */
[data-testid="stSelectbox"] [role="group"] {
    min-height: 2.9rem;
    border: 1px solid var(--gilt-faint) !important;
    border-radius: 2px !important;
    background: var(--velvet-deep) !important;
}
[data-testid="stSelectbox"] [role="group"]:hover { border-color: var(--gilt) !important; }
[data-testid="stSelectbox"] [role="group"]:focus-within {
    outline: 2px solid var(--gilt-bright);
    outline-offset: 3px;
}
[data-testid="stSelectbox"] input {
    background: transparent !important;
    color: var(--candle) !important;
    font-family: var(--body) !important;
    font-size: 1.05rem !important;
}
[data-testid="stSelectbox"] button { background: transparent !important; color: var(--gilt) !important; }
[data-testid="stCheckbox"] label > div:first-of-type {
    border: 1px solid var(--gilt) !important;
    border-radius: 1px !important;
    background-color: var(--velvet-deep) !important;
}
[data-testid="stCheckbox"] input:checked + div, [data-testid="stCheckbox"] label[data-selected] > div:first-of-type {
    background-color: var(--gilt) !important;
}
[data-testid="stCheckbox"] p { color: var(--ash) !important; }
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul {
    border: 1px solid var(--gilt-faint);
    background: var(--velvet-deep) !important;
}
[data-baseweb="popover"] [role="option"] { color: var(--candle); }
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] { background: var(--velvet) !important; }
[data-testid="stWidgetLabel"] p { color: var(--ash); font-size: 1rem; }

/* Expanders */
[data-testid="stExpander"] details {
    border: 1px solid var(--gilt-faint);
    border-radius: 2px;
    background: rgba(31, 14, 26, 0.6);
}
[data-testid="stExpander"] summary:hover { color: var(--gilt-bright); }

/* The pick: a gilt-framed card, the one ornate element on the page */
.st-key-pick_card {
    position: relative;
    padding: 2.4rem 2.2rem 2rem !important;
    border: 1px solid var(--gilt) !important;
    border-radius: 2px !important;
    background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(200, 163, 90, 0.10), transparent 70%),
        linear-gradient(180deg, #2e1526, #1d0d18);
    box-shadow: inset 0 0 0 6px var(--crypt), inset 0 0 0 7px var(--gilt-faint),
                0 30px 70px rgba(0, 0, 0, 0.55);
    text-align: center;
}
.st-key-pick_card::before, .st-key-pick_card::after {
    content: "✦";
    position: absolute; left: 50%; transform: translateX(-50%);
    color: var(--gilt); font-size: 0.85rem; line-height: 1;
    background: var(--crypt); padding: 0 0.5rem;
}
.st-key-pick_card::before { top: -0.45rem; }
.st-key-pick_card::after { bottom: -0.45rem; }
.st-key-pick_card h3 {
    font-size: clamp(1.7rem, 4.5vw, 2.4rem) !important;
    line-height: 1.15;
    text-align: center;
    color: var(--candle);
}
.st-key-pick_card [data-testid="stCaptionContainer"] p { text-align: center; color: var(--gilt); }
.st-key-pick_card [data-testid="stMarkdownContainer"] p { text-align: left; }
.st-key-pick_card [data-testid="stImage"] img {
    border: 1px solid var(--gilt-faint);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
}
.pick-eyebrow {
    font-family: var(--body); font-style: italic; color: var(--ash);
    font-size: 1.05rem; text-align: center; margin: 0;
}

/* Challenge ledger */
.st-key-challenge_card {
    padding: 1.8rem 1.8rem 1.4rem !important;
    border: 1px solid var(--gilt-faint) !important;
    border-radius: 2px !important;
    background: rgba(31, 14, 26, 0.72);
}
[data-testid="stProgressBarTrack"] {
    background: rgba(166, 150, 138, 0.16) !important;
    border-radius: 0 !important;
    height: 4px !important;
}
[data-testid="stProgressBarTrack"] > div {
    background: linear-gradient(90deg, #8c6a2f, var(--gilt-bright)) !important;
    border-radius: 0 !important;
}
[data-testid="stAlert"] {
    border: 1px solid var(--gilt-faint);
    border-radius: 2px;
    background: rgba(42, 19, 34, 0.7) !important;
    color: var(--candle);
}
hr { border-color: var(--gilt-faint); }
.st-key-site_footer [data-testid="stCaptionContainer"] p { text-align: center; font-size: 0.92rem; }

@media (max-width: 640px) {
    .block-container { padding: 2.2rem 1rem 3rem; }
    .st-key-pick_card { padding: 2rem 1.2rem 1.6rem !important; }
    .st-key-challenge_card { padding: 1.3rem 1rem !important; }
    .st-key-challenge_card h2 { font-size: 1.2rem; }
    .st-key-challenge_card h3, .st-key-challenge_card h4 { font-size: 0.98rem; }
    .st-key-category_row [data-testid="stButton"] button { min-height: 3rem; }
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
    left, right = st.columns(2)
    if category == "movie":
        genre_options = sorted(
            {item["genre"] for item in load_recommendations(CATEGORIES[category][1])}
        )
        genre = left.selectbox(
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
        scare_level = right.selectbox(
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
            "show": left.selectbox(
                "Show",
                [ANY_FILTER, *shows],
                key=filter_widget_key(category, "show"),
            )
        }

    games = load_recommendations(CATEGORIES[category][1])
    genres = sorted({item["genre"] for item in games})
    genre = left.selectbox(
        "Genre",
        [ANY_FILTER, *genres],
        key=filter_widget_key(category, "genre"),
    )
    player_support = right.selectbox(
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
            marker = "tonight"
            accessible_label = f"October {day}, today, not completed"
            classes.append("is-today")
        elif challenge_date > today:
            marker = "·"
            accessible_label = f"October {day}, upcoming"
            classes.append("is-upcoming")
        else:
            marker = ""
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
            gap: 4px;
            margin: .6rem 0 1rem;
        }
        .october-weekday {
            color: var(--ash);
            font-family: var(--body);
            font-style: italic;
            font-size: .95rem;
            padding: .2rem 0 .35rem;
            text-align: center;
        }
        .october-day {
            align-items: center;
            aspect-ratio: 1 / 1;
            background: rgba(23, 12, 20, .7);
            border: 1px solid rgba(200, 163, 90, .14);
            border-radius: 1px;
            color: var(--candle);
            display: flex;
            flex-direction: column;
            gap: .15rem;
            justify-content: center;
            min-height: 2.6rem;
            overflow: hidden;
        }
        .october-day strong {
            font-family: var(--display);
            font-size: 1.05rem;
            font-weight: 600;
            line-height: 1;
        }
        .october-day span { color: var(--ash); font-size: .78rem; line-height: 1; }
        .october-day.is-empty { background: transparent; border-color: transparent; }
        .october-day.is-completed {
            background: radial-gradient(circle at 50% 40%, rgba(122, 30, 34, .85), rgba(74, 16, 22, .9));
            border-color: rgba(200, 163, 90, .55);
        }
        .october-day.is-completed strong { color: var(--gilt-bright); }
        .october-day.is-today { border-color: var(--gilt-bright); box-shadow: inset 0 0 0 1px var(--gilt-bright), 0 0 18px rgba(230, 201, 131, .25); }
        .october-day.is-today span { color: var(--gilt-bright); }
        .october-day.is-upcoming { color: rgba(241, 228, 198, .62); }
        .october-day.is-past { opacity: .5; }
        @media (max-width: 520px) {
            .october-challenge-calendar { gap: 3px; }
            .october-day { min-height: 2.2rem; }
            .october-day strong { font-size: .88rem; }
            .october-day span { font-size: .62rem; }
            .october-weekday { font-size: .78rem; }
        }
        </style>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="challenge_card"):
        st.markdown(f"## The {today.year} October challenge")
        if status == "active":
            st.markdown(f"### Night {today.day} of {CHALLENGE_NIGHTS}")
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
                    st.markdown(f"Tonight’s pick is {icon} {pick_title}. Use Complete Tonight when you’ve finished it.")
                else:
                    st.caption("Choose a movie, episode, or game above to get tonight’s pick.")
        elif status == "upcoming":
            st.markdown(f"### Challenge opens October 1, {today.year}")
            st.caption(f"Today is {today.strftime('%B')} {today.day}.")
        elif nights == CHALLENGE_NIGHTS:
            st.success(f"All {CHALLENGE_NIGHTS} October nights are complete.")
        else:
            st.markdown(f"### October {today.year} has ended")
            st.caption(f"Final progress: {nights} of {CHALLENGE_NIGHTS} nights.")

        st.markdown(f"#### {nights} of {CHALLENGE_NIGHTS} nights complete")
        st.progress(nights / CHALLENGE_NIGHTS)
        st.caption(f"{percentage}% of October")

        st.markdown(_challenge_calendar_markup(today, year_completions), unsafe_allow_html=True)
        st.caption("Completed nights glow red and show what you chose: 🎬 movie, 📺 episode, 🎮 game.")

        if year_completions:
            with st.expander(f"Every night so far ({len(year_completions)})"):
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
                "This erases every completed night for the challenge. "
                "Your watched-movie list stays as it is."
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
with st.container(key="hero"):
    st.title("31 Nights")
    st.markdown('<div class="gilt-rule" aria-hidden="true"><span>✦</span></div>', unsafe_allow_html=True)
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

with st.container(key="category_row"):
    col1, col2, col3 = st.columns(3)
    for column, category in zip((col1, col2, col3), CATEGORIES):
        with column:
            if st.button(CATEGORIES[category][0], use_container_width=True):
                st.session_state.category = category
                st.session_state.recommendation = None
                st.session_state.filters = {}
                st.session_state.filter_version += 1

if st.session_state.category is not None:
    category = st.session_state.category
    # Layout slots, in reading order. The watched-movie controls sit at the
    # bottom but are filled first, because they decide which picks are eligible.
    filters_area = st.container()
    notices_area = st.container()
    pick_area = st.container()
    actions_area = st.container()
    watched_area = st.container()

    with filters_area:
        filters = show_filters(category)
    st.session_state.filters = filters
    all_matches = recommendations_for(category, filters, today)
    matches = all_matches
    watched_keys = set()
    include_watched = False

    if category == "movie":
        with watched_area:
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
    with notices_area:
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

    if recommendation is not None:
        enrichment = None
        if category == "movie":
            enrichment = cached_movie_enrichment(
                recommendation["title"], recommendation["year"],
                os.getenv("TMDB_READ_ACCESS_TOKEN", ""),
            )
        pick_label = (
            "Tonight’s pick"
            if challenge_status(today) == "active" and completion_for_date(challenge_completions, today) is None
            else "Your recommendation"
        )
        with pick_area:
            with st.container(border=True, key="pick_card"):
                st.markdown(f'<p class="pick-eyebrow">{pick_label}</p>', unsafe_allow_html=True)
                show_recommendation(category, recommendation, enrichment)

    with actions_area:
        if challenge_status(today) == "active":
            if completion_for_date(challenge_completions, today):
                st.caption("Tonight is already complete. You can keep browsing, but a second completion cannot be added for this date.")
            elif st.button("Complete Tonight", key=f"complete_tonight_{today.isoformat()}", type="primary", use_container_width=True):
                try:
                    updated_completions = add_challenge_completion(
                        challenge_completions, category, recommendation, today
                    )
                    save_challenge_completions(updated_completions, challenge_store_path)
                except ChallengeError as error:
                    st.error(str(error))
                else:
                    st.rerun()

        if category == "movie" and recommendation is not None:
            current_key = movie_history_key(recommendation)
            if current_key in watched_keys:
                st.caption("You’ve seen this one. Future movie rolls skip it unless you include watched movies.")

        if category == "movie" and recommendation is not None and movie_history_key(recommendation) not in watched_keys:
            roll_col, watched_col, change_col = st.columns(3)
        else:
            roll_col, change_col = st.columns(2)
            watched_col = None
        with roll_col:
            if st.button("🎲 Roll Again", disabled=not matches, use_container_width=True):
                st.session_state.recommendation = random.choice(matches)
                st.session_state.recommendation_date = today.isoformat()
                st.session_state.marked_movie_key = None
                st.rerun()
        if watched_col is not None:
            with watched_col:
                if st.button("Mark as Watched", key=f"mark_watched_{st.session_state.filter_version}", use_container_width=True):
                    watched_keys.add(movie_history_key(recommendation))
                    save_watched_movies(watched_keys, watched_history_path)
                    st.session_state.marked_movie_key = movie_history_key(recommendation)
                    st.rerun()
        with change_col:
            if st.button("🔄 Choose Something Else", use_container_width=True):
                st.session_state.category = None
                st.session_state.recommendation = None
                st.session_state.filters = {}
                st.session_state.filter_version += 1
                st.session_state.marked_movie_key = None
                st.rerun()

st.markdown('<div class="gilt-rule" aria-hidden="true"><span>✦</span></div>', unsafe_allow_html=True)
show_challenge_card(today, challenge_completions, challenge_store_path)

coming_soon = coming_soon_episodes(today)
if coming_soon:
    st.markdown("#### Coming soon")
    for episode in coming_soon:
        st.write(
            f"{episode['show']}: {episode['episode_title']} · "
            f"Available {episode.get('available_date', 'Date not set')}"
        )

with st.container(key="site_footer"):
    st.caption(
        "On the public demo, watch and challenge history is shared by every visitor "
        "and may reset when the app restarts."
    )
