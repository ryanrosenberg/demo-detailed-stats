import streamlit as st
import utils
from htbuilder import div, p
import json

def app(tournaments):
    st.title('QB League Season 2 -- Questions')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)
    st.markdown('''<style>
    .buzz {display: inline; background-color: #e4e1e2;}
    .buzz-value {display: inline; background-color: #e4e1e2; font-size: 80%; color: #555555;}
    p {display: inline;}
    .row_heading.level0 {display:none}
    .stDataFrame {border:1px solid white}
    .blank {display:none}
    </style>''',
                unsafe_allow_html=True)

    buzzes = utils.load_buzzes()
    tossup_meta = utils.load_tossup_meta()

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]
    
    if len(tournaments) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(tournaments)]

    pac = st.selectbox('Packet', options = range(1, 10))
    tu = st.selectbox('Tossup', options = range(1, 21), format_func= lambda x: str(x) + ' (' + full_buzzes['answer'][full_buzzes['packet'] == pac][full_buzzes['tossup'] == x].unique()[0] + ')')

    packets = utils.get_packets()

    sani = packets[pac - 1]['tossups'][tu - 1]['question'].split(' ')
    qbuzz = full_buzzes[full_buzzes['packet'] == pac][buzzes['tossup'] == tu]
    for i, row in qbuzz.iterrows():
        sani[row['buzz_position']] = str(
            div(_class = 'buzz')(
                sani[row['buzz_position']],
                p(_class = 'buzz-value')(' ' + str(row['buzz_value']))
                )
        )

    sani = ' '.join(sani)

    st.markdown(sani,
    unsafe_allow_html=True)
    st.markdown('ANSWER: ' + packets[pac - 1]['tossups'][tu - 1]['answer'],
    unsafe_allow_html=True)

    qbuzz['packet'] = qbuzz['packet'].astype(int)
    qbuzz = qbuzz[['player', 'team', 'buzz_value', 'buzz_position']]
    st.dataframe(qbuzz.sort_values('buzz_position', ascending=True))
    

    