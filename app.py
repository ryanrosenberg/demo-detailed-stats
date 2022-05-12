import players
import teams
import categories
import questions
import tossups
import bonuses
import games
import streamlit as st
st.set_page_config(layout="wide")

PAGES = {
    "Players": players,
    "Teams": teams,
    "Categories": categories,
    "Questions": questions,
    "Tossups": tossups,
    "Bonuses": bonuses,
    "Games" : games
}
st.sidebar.title('Navigation')
selection = st.sidebar.selectbox("Go to", list(PAGES.keys()))
tournaments = st.sidebar.multiselect("Divisions", ['01', '2a', '2b', '3a', '3b'], format_func=lambda x: '1' if x == '01' else x)

page = PAGES[selection]
page.app(tournaments)