import streamlit as st
import utils

def app(tournaments, accent_color):
    st.title('QB League Season 2 -- Tossups')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
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
        power_pct = lambda x: round(x.P/x.Games, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.Games, 3), 
        neg_pct = lambda x: round(x.N/x.Games, 3)
        )

    category_summary = tossup_table.groupby(['category'], as_index=False).agg(
        {'Games': 'sum', 'P': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        power_pct = lambda x: round(x.P/x.Games, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.Games, 3), 
        neg_pct = lambda x: round(x.N/x.Games, 3)
        )
    subcategory_summary = tossup_table.groupby(['category', 'subcategory'], as_index=False).agg(
        {'Games': 'sum', 'P': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        power_pct = lambda x: round(x.P/x.Games, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.Games, 3), 
        neg_pct = lambda x: round(x.N/x.Games, 3)
        )
    
    st.header('Category Summary')
    utils.aggrid_interactive_table(category_summary)    
    st.header('Subcategory Summary')
    utils.aggrid_interactive_table(subcategory_summary) 
    st.header('All Tossups')         
    utils.aggrid_interactive_table(tossup_table)