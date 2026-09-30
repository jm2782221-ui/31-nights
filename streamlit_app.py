from datetime import date
import json
import os
from pathlib import Path
import random

import streamlit as st
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


@st.cache_data
def load_recommendations(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as data_file:
        return json.load(data_file)


def days_until_halloween():
    today = date.today()
    halloween = date(today.year, 10, 31)

    if today > halloween:
        halloween = date(today.year + 1, 10, 31)
    return (halloween - today).days


def recommendations_for(category, filters):
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


def choose_recommendation(category, filters):
    recommendations = recommendations_for(category, filters)
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

                providers = enrichment.get("watch_providers")
                if isinstance(providers, dict):
                    raw_streaming = providers.get("streaming")
                    streaming = []
                    if isinstance(raw_streaming, list):
                        streaming = [
                            name.strip()
                            for name in raw_streaming
                            if isinstance(name, str) and name.strip()
                        ]

                    if streaming:
                        st.caption("Available on in the U.S.")
                        for name in streaming:
                            st.text(f"- {name}")
                    else:
                        st.caption("No U.S. streaming providers are listed for this movie.")
                    st.caption("Availability data by JustWatch via TMDB; listings can change.")
        st.caption("Movie details provided by TMDB. Not endorsed or certified by TMDB.")
    elif category == "episode":
        st.subheader(f'{recommendation["show"]}: {recommendation["episode_title"]}')
        st.caption(
            f'Season {recommendation["season"]}, '
            f'Episode {recommendation["episode_number"]}'
        )
    else:
        st.subheader(recommendation["title"])
        st.caption(
            f'{recommendation["genre"]} · '
            f'{recommendation["player_support"].replace("-", " ").title()}'
        )


st.title("31 Nights 🎃")
st.subheader(f"{days_until_halloween()} days until Halloween!")
st.write("What do you want to roll?")

if "category" not in st.session_state:
    st.session_state.category = None
if "recommendation" not in st.session_state:
    st.session_state.recommendation = None
if "filters" not in st.session_state:
    st.session_state.filters = {}
if "filter_version" not in st.session_state:
    st.session_state.filter_version = 0

col1, col2, col3 = st.columns(3)
for column, category in zip((col1, col2, col3), CATEGORIES):
    with column:
        if st.button(CATEGORIES[category][0], use_container_width=True):
            st.session_state.category = category
            st.session_state.recommendation = None
            st.session_state.filters = {}
            st.session_state.filter_version += 1

if st.session_state.category is not None:
    st.session_state.filters = show_filters(st.session_state.category)
    matches = recommendations_for(
        st.session_state.category, st.session_state.filters
    )
    if st.session_state.recommendation not in matches:
        st.session_state.recommendation = random.choice(matches) if matches else None

    if st.session_state.recommendation is None:
        st.info("No recommendations match those filters. Try another combination.")
    else:
        enrichment = None
        if st.session_state.category == "movie":
            enrichment = cached_movie_enrichment(
                st.session_state.recommendation["title"],
                st.session_state.recommendation["year"],
                os.getenv("TMDB_READ_ACCESS_TOKEN", ""),
            )
        with st.container(border=True):
            show_recommendation(
                st.session_state.category,
                st.session_state.recommendation,
                enrichment,
            )

    roll_col, change_col = st.columns(2)
    with roll_col:
        if st.button(
            "🔄 Roll Again",
            disabled=not matches,
            use_container_width=True,
        ):
            st.session_state.recommendation = choose_recommendation(
                st.session_state.category, st.session_state.filters
            )
            st.rerun()
    with change_col:
        if st.button("↩️ Choose Something Else", use_container_width=True):
            st.session_state.category = None
            st.session_state.recommendation = None
            st.session_state.filters = {}
            st.session_state.filter_version += 1
            st.rerun()
