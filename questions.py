import streamlit as st
import utils
from htbuilder import div, p
import json

def app(tournaments, accent_color):
    st.title('QB League Season 2 -- Questions')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)

    buzzes = utils.load_buzzes()
    bonuses = utils.load_bonuses()
    tossup_meta = utils.load_tossup_meta()
    bonus_meta = utils.load_bonus_meta()

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]

    full_bonuses = bonuses.merge(bonus_meta[bonus_meta['season'] == 2], on=['packet', 'bonus'])
    full_bonuses['division'] = [x.split('-')[1] for x in full_bonuses['game_id']]

    if len(tournaments) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(tournaments)]
        full_bonuses = full_bonuses[full_bonuses['division'].isin(tournaments)]

    pac = st.selectbox('Packet', options = range(1, 10))
    question_type = st.selectbox('Question Type', options = ['Tossup', 'Bonus'])
    if question_type == 'Tossup':
        tu = st.selectbox('Question Number', options = range(1, 21), format_func= lambda x: str(x) + ' (' + full_buzzes['answer'][full_buzzes['packet'] == pac][full_buzzes['tossup'] == x].unique()[0] + ')')
    else:
        tu = st.selectbox('Question Number', options = range(1, 21), format_func= lambda x: str(x) + ' (' + full_bonuses['answers'][full_bonuses['packet'] == pac][full_bonuses['bonus'] == x].unique()[0] + ')')

    packets = utils.get_packets()

    if question_type == 'Tossup':
        sani = packets[pac - 1]['tossups'][tu - 1]['question'].split(' ')
        qbuzz = full_buzzes[full_buzzes['packet'] == pac][full_buzzes['tossup'] == tu]
        
        for i, row in qbuzz.iterrows():
            if row['buzz_value'] in [15, 10]:
                sani[row['buzz_position']] = str(
                    div(_class = 'buzz')(
                        sani[row['buzz_position']],
                        p(_class = 'buzz-value correct-buzz-value')(' ' + str(row['buzz_value']))
                        )
                )
            else:
                sani[row['buzz_position']] = str(
                    div(_class = 'buzz')(
                        sani[row['buzz_position']],
                        p(_class = 'buzz-value incorrect-buzz-value')(' ' + str(row['buzz_value']))
                        )
                )

        sani = ' '.join(sani)

        st.markdown(sani,
    unsafe_allow_html=True)
        st.markdown('ANSWER: ' + packets[pac - 1]['tossups'][tu - 1]['answer'],
    unsafe_allow_html=True)
        qbuzz['packet'] = qbuzz['packet'].astype(int)
        qbuzz = qbuzz[['player', 'team', 'buzz_value', 'buzz_position']]
        st.subheader('Buzzes')
        utils.aggrid_interactive_table(qbuzz.sort_values('buzz_position', ascending=True))

    else:
        qbonus = full_bonuses[full_bonuses['packet'] == pac][full_bonuses['bonus'] == tu]
        bonus_summary = qbonus.assign(
        part1_value = lambda x: x.part1_value/10, part2_value = lambda x: x.part2_value/10, part3_value = lambda x: x.part3_value/10
        ).groupby(['packet', 'bonus', 'category', 'subcategory', 'answers']).agg(
            {'part1_value': 'mean', 'part2_value': 'mean', 'part3_value': 'mean'}
            ).reset_index()
        qbonus = qbonus[['category', 'subcategory', 'team', 'part1_value', 'part2_value', 'part3_value']]

        st.markdown(packets[pac - 1]['bonuses'][tu - 1]['leadin'],
                    unsafe_allow_html=True)
        for i in range(0, 3):
            conv = [i for i in bonus_summary[f'part{i+1}_value']]
            
            st.markdown(f""" <p style='size:80%; color: #A3A3A3'>{round(conv[0]*100)}% |</p>
            [10{packets[pac - 1]['bonuses'][tu - 1]['difficultyModifiers'][i]}] {packets[pac - 1]['bonuses'][tu - 1]['parts'][i]}""",
                    unsafe_allow_html=True)
            st.markdown('ANSWER: ' + packets[pac - 1]['bonuses'][tu - 1]['answers'][i],
                    unsafe_allow_html=True)
        
        utils.aggrid_interactive_table(qbonus)
    

    