from datetime import date
import json
from pathlib import Path
import random

import streamlit as st


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


def show_recommendation(category, recommendation):
    if category == "movie":
        st.subheader(recommendation["title"])
        st.caption(
            f'{recommendation["year"]} · {recommendation["genre"]} · '
            f'Scare level {recommendation["scare_level"]}/5'
        )
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
        show_recommendation(st.session_state.category, st.session_state.recommendation)

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
