import streamlit as st
st.set_page_config(layout="wide")
import utils
import pandas as pd

for k, v in st.session_state.items():
    st.session_state[k] = v

utils.local_css("style.css")

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

accent_color = "#ff4b4b"

st.markdown("""<h1>Welcome!</h1><br><span class="material-symbols-outlined">
keyboard_double_arrow_left
</span><br>
Check out one of the stats pages on the left.""",
unsafe_allow_html=True)

utils.hr()
st.header('Glossary')
gloss = {
    'Term': [
        '<b>ACC</b>', 
        '<b>BPA</b>', 
        '<b>Easy.Conv</b>, <b>Med.Conv</b>, <b>Hard.Conv</b>',
        '<b>Conv.</b>', 
        '<b>Neg.</b>', 
        '<b>PPB</b>', 
        '<b>PPG</b>'
        ],
    'Definition': [
        'Buzzpoint AUC. The area under the curve of a player/team\'s <a href = "https://hsquizbowl.org/forums/viewtopic.php?t=21962">buzzpoint curve</a>.', 
        'Average correct celerity. The average % of a question remaining when a player/team buzzed correctly.',
        'Conversion percentage for the bonus part with the given difficulty. Difficulty was assigned based on which part was converted most/least.',
        'Conversion percentage. The number of rooms where the tossup(s) were converted.',
        'Neg percentage. The number of rooms where the tossup(s) were negged.',
        'Points per bonus',
        'Points per game'
        ]
    }

utils.df_to_kable(pd.DataFrame(gloss))
# col1, col2 = st.columns(2)
# with col1:
#     qbjs = st.file_uploader("Upload QBJs", accept_multiple_files=True)
# with col2:
#     packets = st.file_uploader("Upload parsed packets", accept_multiple_files=True)

# if len(qbjs) > 0:
#     utils.populate_db_qbjs(qbjs)

# if len(packets) > 0:
#     utils.populate_db_packets(packets)

# with st.spinner("Processing files..."):
    # utils.populate_db_qbjs_nasat()
    # utils.populate_db_packets_nasat()
