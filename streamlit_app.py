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


def choose_recommendation(category):
    _, filename = CATEGORIES[category]
    return random.choice(load_recommendations(filename))


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

col1, col2, col3 = st.columns(3)
for column, category in zip((col1, col2, col3), CATEGORIES):
    with column:
        if st.button(CATEGORIES[category][0], use_container_width=True):
            st.session_state.category = category
            st.session_state.recommendation = choose_recommendation(category)

if st.session_state.recommendation is not None:
    show_recommendation(st.session_state.category, st.session_state.recommendation)

    roll_col, change_col = st.columns(2)
    with roll_col:
        if st.button("🔄 Roll Again", use_container_width=True):
            st.session_state.recommendation = choose_recommendation(
                st.session_state.category
            )
            st.rerun()
    with change_col:
        if st.button("↩️ Choose Something Else", use_container_width=True):
            st.session_state.category = None
            st.session_state.recommendation = None
            st.rerun()
