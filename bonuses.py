from numpy import full
import streamlit as st
import utils

def app(tournaments):
    st.title('QB League Season 2 -- Bonuses')
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
    
    bonuses = utils.load_bonuses()
    bonus_meta = utils.load_bonus_meta()
    packets = utils.get_packets()
    full_bonuses = bonuses.merge(bonus_meta[bonus_meta['season'] == 2], on=['packet', 'bonus'])
    full_bonuses['division'] = [x.split('-')[1] for x in full_bonuses['game_id']]
    
    if len(tournaments) > 0:
        full_bonuses = full_bonuses[full_bonuses['division'].isin(tournaments)]

    bonus_summary = full_bonuses.assign(
        part1_value = lambda x: x.part1_value/10, part2_value = lambda x: x.part2_value/10, part3_value = lambda x: x.part3_value/10
        ).groupby(['packet', 'bonus', 'category', 'subcategory', 'answers']).agg(
            {'part1_value': 'mean', 'part2_value': 'mean', 'part3_value': 'mean'}
            ).reset_index()
    bonus_answers = [answers.split(' / ') for answers in bonus_summary['answers']]

    easy_parts = []
    med_parts = []
    hard_parts = []
    for i, row in bonus_summary.iterrows():
        # print(f"{i} {int(row['packet'])} - {row['bonus']}")
        # print(f"{int(row['packet']) - 1} {row['bonus']-1}")
        easy_answer = bonus_answers[i][packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('e')]
        med_answer = bonus_answers[i][packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('m')]
        hard_answer = bonus_answers[i][packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('h')]
        easy_conv = row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('e') + 1}_value"]
        med_conv = row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('m') + 1}_value"]
        hard_conv = row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('h') + 1}_value"]
        easy_parts.append({'answer': easy_answer, 'conv': round(easy_conv, 3)})
        med_parts.append({'answer': med_answer, 'conv': round(med_conv, 3)})
        hard_parts.append({'answer': hard_answer, 'conv': round(hard_conv, 3)})
    
    bonus_summary = bonus_summary[['packet', 'bonus', 'category', 'subcategory']]
    bonus_summary['easy'] = [part['answer'] for part in easy_parts]
    bonus_summary['easy_conv'] = [part['conv'] for part in easy_parts]
    bonus_summary['medium'] = [part['answer'] for part in med_parts]
    bonus_summary['medium_conv'] = [part['conv'] for part in med_parts]
    bonus_summary['hard'] = [part['answer'] for part in hard_parts]
    bonus_summary['hard_conv'] = [part['conv'] for part in hard_parts]
    bonus_summary['packet'] = bonus_summary['packet'].astype(int)

    ordered_bonuses = full_bonuses
    easy_order = []
    med_order = []
    hard_order = []
    for i, row in ordered_bonuses.iterrows():
        easy_order.append(row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('e') + 1}_value"])
        med_order.append(row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('m') + 1}_value"])
        hard_order.append(row[f"part{packets[int(row['packet']) - 1]['bonuses'][row['bonus']-1]['difficultyModifiers'].index('h') + 1}_value"])
    ordered_bonuses['easy'] = easy_order
    ordered_bonuses['medium'] = med_order
    ordered_bonuses['hard'] = hard_order

    ordered_bonuses = ordered_bonuses[['packet', 'bonus', 'team', 'easy', 'medium', 'hard']]
    ordered_bonuses['packet'] = ordered_bonuses['packet'].astype(int)
    selection = utils.aggrid_interactive_table(bonus_summary)
    if selection["selected_rows"]:
        team_bonuses = ordered_bonuses[ordered_bonuses['packet'] == selection["selected_rows"][0]['packet']][ordered_bonuses['bonus'] == selection["selected_rows"][0]['bonus']]
        st.dataframe(team_bonuses)
