import streamlit as st
import utils
from htbuilder import div, p
import json

def app():
    st.title('QB League Season 2 Divison 1 -- Questions')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)
    st.markdown('''<style>
    .buzz {display: inline; background-color: #e4e1e2;}
    .buzz-value {display: inline; background-color: #e4e1e2; font-size: 80%; color: #555555;}
    p {display: inline;}
    </style>''',
                unsafe_allow_html=True)

    buzzes, bonuses, tossup_meta = utils.load_data()
    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])

    pac = st.selectbox('Packet', options = range(1, 10))
    tu = st.selectbox('Tossup', options = range(1, 21), format_func= lambda x: str(x) + ' (' + full_buzzes['answer'][full_buzzes['packet'] == pac][full_buzzes['tossup'] == x].unique()[0] + ')')

    with open(f'packet{pac}.json', 'r') as f:
        question_text = json.load(f)

    sani = question_text['tossups'][tu - 1]['question'].split(' ')
    qbuzz = buzzes[buzzes['packet'] == pac][buzzes['tossup'] == tu]
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
    st.markdown('ANSWER: ' + question_text['tossups'][tu - 1]['answer'],
    unsafe_allow_html=True)

    qbuzz['packet'] = qbuzz['packet'].astype(int)
    st.dataframe(qbuzz.sort_values('buzz_position', ascending=True))
    

    