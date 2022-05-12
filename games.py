import streamlit as st
import utils

def app(tournaments):
    st.title('QB League Season 2 -- Games')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)
    st.markdown('''<style>
    .buzz {display: inline; background-color: #e4e1e2;}
    .buzz-value {display: inline; background-color: #e4e1e2; font-size: 80%; color: #555555;}
    p {display: inline;}
    </style>''',
                unsafe_allow_html=True)
    
    buzzes = utils.load_buzzes()
    tossup_meta = utils.load_tossup_meta()

    games, scoresheets = st.columns(2)
    st.write('Under construction!')
    