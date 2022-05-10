import players
import teams
import categories
import questions
import streamlit as st
st.set_page_config(layout="wide")

PAGES = {
    "Players": players,
    "Teams": teams,
    "Categories": categories,
    "Questions": questions
}
st.sidebar.title('Navigation')
selection = st.sidebar.selectbox("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app()