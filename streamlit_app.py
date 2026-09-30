from datetime import date
import streamlit as st

def days_until_halloween():
    today = date.today()
    halloween = date(today.year, 10, 31)

    if today > halloween:
        halloween = date(today.year + 1, 10, 31)
    return (halloween - today).days

st.title("31 Nights 🎃")    

days_left = days_until_halloween()

st.subheader(f"{days_left} days until Halloween!")

st.write("What do you want to roll?")

col1, col2, col3 = st.columns(3)

with col1:
    st.button("🎬 MOVIE")
with col2:
    st.button("📺 HALLOWEEN EPISODE")
with col3:
    st.button("🎮 SPOOKY GAME")