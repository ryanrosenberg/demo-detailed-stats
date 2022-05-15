import streamlit as st
import utils

def app(tournaments, accent_color):
    st.title('QB League Season 2 -- Players')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)

    buzzes = utils.load_buzzes()
    tossup_meta = utils.load_tossup_meta()

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]
    
    if len(tournaments) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(tournaments)]
    player_summary = full_buzzes.groupby(
            ['player', 'team', 'buzz_value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['player', 'team'], columns='buzz_value', values=0
                    ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    player_cat_ranks = full_buzzes.groupby(['player', 'team', 'category', 'buzz_value']).agg(
                'size'
                ).reset_index().pivot(
                    index = ['player', 'team', 'category'], columns='buzz_value', values=0
                    ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    player_summary = utils.fill_out_tossup_values(player_summary)
    player_cat_ranks = utils.fill_out_tossup_values(player_cat_ranks)

    player_summary = player_summary[['player', 'team', 'P', 'G', 'N']].fillna(0).assign(
                        Pts = lambda x: x.P*15 + x.G*10 - x.N*5
                        ).sort_values(['Pts'], ascending=False)

    player_cat_ranks = player_cat_ranks[['player', 'team', 'category', 'P', 'G', 'N']].fillna(0).assign(
                        Pts = lambda x: x.P*15 + x.G*10 - x.N*5
                        )
    player_cat_ranks['rank'] = player_cat_ranks.groupby('category')['Pts'].rank('min', ascending=False)


    st.write("Click on a player's row to show more information!")
    selection = utils.aggrid_interactive_table(player_summary, accent_color=accent_color)
    
    if selection["selected_rows"]:
        st.subheader(f"{selection['selected_rows'][0]['player']}, {selection['selected_rows'][0]['team']}")
        player_buzzes = full_buzzes[full_buzzes['player'] == selection["selected_rows"][0]['player']][full_buzzes['team'] == selection["selected_rows"][0]['team']]
        player_cats = player_buzzes.groupby(
            ['player', 'team', 'category', 'buzz_value']
            ).agg('size').reset_index().pivot(
            index = ['player', 'team', 'category'], columns='buzz_value', values=0
            ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        player_cats = utils.fill_out_tossup_values(player_cats)
                
        player_cats = player_cats[['player', 'team', 'category', 'P', 'G', 'N']].fillna(0).assign(Pts = lambda x: x.P*15 + x.G*10 - x.N*5)
        player_cats[['P', 'G', 'N', 'Pts']] = player_cats[['P', 'G', 'N', 'Pts']].astype(int).sort_values(['Pts'], ascending=False)

        st.subheader('Categories')
        col1, col2 = st.columns(2)
        player_rank = player_cats.merge(player_cat_ranks[['player', 'team', 'category', 'rank']], on=['player', 'team', 'category'])
        player_rank = player_rank[['category', 'P', 'G', 'N', 'Pts', 'rank']].rename(columns={'rank': 'Rk'})
        player_rank['Rk'] = player_rank['Rk'].astype(int)
        
        with col1:
            utils.aggrid_interactive_table(player_rank, accent_color=accent_color)
        negs = col2.checkbox("Add negs?")
        col2.altair_chart(utils.make_category_buzz_chart(player_buzzes, negs))
        
        player_subcats = player_buzzes.groupby(['category', 'subcategory', 'buzz_value']).agg(
        'size'
        ).reset_index().pivot(
            index = ['category', 'subcategory'], columns='buzz_value', values=0
            ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        player_subcats = utils.fill_out_tossup_values(player_subcats)

        player_subcats = player_subcats[['category', 'subcategory', 'P', 'G', 'N']].fillna(0).assign(Pts = lambda x: x.P*15 + x.G*10 - x.N*5)
        player_subcats[['P', 'G', 'N', 'Pts']] = player_subcats[['P', 'G', 'N', 'Pts']].astype(int).sort_values(['Pts'], ascending=False)

        col1.subheader('Subcategories')
        with col1:
            utils.aggrid_interactive_table(player_subcats, accent_color=accent_color)
        # col4.pyplot(utils.make_subcategory_buzz_chart(player_buzzes))

        st.subheader('Buzzes')
        player_buzzes['packet'] = player_buzzes['packet'].astype(int)
        packets = utils.get_packets()
        contexts = []
        for i, row in player_buzzes.iterrows():
            packet_sani = packets[row['packet'] - 1]['tossups'][row['tossup'] - 1]['question_sanitized'].split(' ')
            context = packet_sani[row['buzz_position']-8:row['buzz_position']]
            contexts.append(' '.join(context))

        player_buzzes['context'] = [context + ' | *buzz* |' for context in contexts]
        utils.aggrid_interactive_table(player_buzzes[['packet', 'tossup', 'category', 'subcategory', 'answer', 'buzz_position', 'buzz_value', 'context']], accent_color=accent_color)


