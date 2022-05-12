import streamlit as st
import utils

def app(tournaments):
    st.title('QB League Season 2 -- Tossups')
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
    
    tossup_summary = full_buzzes.groupby(
            ['packet', 'tossup', 'category', 'subcategory', 'answer', 'buzz_value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['packet', 'tossup', 'category', 'subcategory', 'answer',], columns='buzz_value', values=0
                    ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    packet_games = full_buzzes.groupby('packet').agg(
        {'game_id': 'nunique'}
        ).reset_index().rename(columns={'game_id': 'Games'})
    packet_games[['packet']] = packet_games[['packet']].astype(int)

    tossup_table = tossup_summary.merge(packet_games, on = 'packet')
    tossup_table = tossup_table[['packet', 'tossup', 'category', 'subcategory', 'answer', 'Games', 'P', 'G', 'N']].fillna(0)
    tossup_table[['packet', 'P', 'G', 'N']] = tossup_table[['packet', 'P', 'G', 'N']].astype(int)
    tossup_table = tossup_table.assign(
        power_pct = lambda x: x.P/x.Games, conv_pct = lambda x: (x.P + x.G)/x.Games, neg_pct = lambda x: x.N/x.Games)
    st.dataframe(tossup_table, height = 500)