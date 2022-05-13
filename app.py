import players
import teams
import categories
import questions
import tossups
import bonuses
import games
import streamlit as st
st.set_page_config(layout="wide")
from streamlit_option_menu import option_menu

PAGES = {
    "Players": players,
    "Teams": teams,
    "Categories": categories,
    "Questions": questions,
    "Tossups": tossups,
    "Bonuses": bonuses,
    "Games" : games
}

st.markdown('''<style>
    .buzz {display: inline; background-color: #e4e1e2;}
    .buzz-value {display: inline; background-color: #e4e1e2; font-size: 80%;}
    .buzz-value.correct-buzz-value {color: #555555;}
    .buzz-value.incorrect-buzz-value {color: #ff4b4b;}
    p {display: inline;}
    .row_heading.level0 {display:none}
    .stDataFrame {border:1px solid white}
    .data {font-size: 12px;}
    .blank {display:none}
    .ag-header-row {background-color: blue !important;}
    </style>''',
                unsafe_allow_html=True)
with st.sidebar:
    selection = option_menu("Go to", list(PAGES.keys()),
    menu_icon="arrow-down-right",
    styles={
        "menu-title": {"font-size": "20px", "text-align": "left", "margin":"0px"},
        "container": {"padding": "0!important", "background-color": "#F0F2F6"},
        "icon": {"color": "black", "font-size": "16px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
    })

st.sidebar.subheader('Filters')
tournaments = st.sidebar.multiselect("Divisions", ['01', '2a', '2b', '3a', '3b'], format_func=lambda x: '1' if x == '01' else x)

page = PAGES[selection]
page.app(tournaments)