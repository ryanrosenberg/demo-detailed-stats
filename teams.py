import streamlit as st
import utils

def app(tournaments, accent_color):
    st.title('QB League Season 2 -- Teams')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)

    buzzes = utils.load_buzzes()
    bonuses = utils.load_bonuses()
    tossup_meta = utils.load_tossup_meta()
    bonus_meta = utils.load_bonus_meta()

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]
    
    if len(tournaments) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(tournaments)]

    team_summary = full_buzzes.groupby(
            ['team', 'buzz_value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['team'], columns='buzz_value', values=0
                    ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    team_cat_ranks = full_buzzes.groupby(['team', 'category', 'buzz_value']).agg(
                'size'
                ).reset_index().pivot(
                    index = ['team', 'category'], columns='buzz_value', values=0
                    ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    team_summary = utils.fill_out_tossup_values(team_summary)
    team_cat_ranks = utils.fill_out_tossup_values(team_cat_ranks)

    team_summary = team_summary[['team', 'P', 'G', 'N']].fillna(0).assign(
                        Pts = lambda x: x.P*15 + x.G*10 - x.N*5
                        ).sort_values(['Pts'], ascending=False)

    team_cat_ranks = team_cat_ranks[['team', 'category', 'P', 'G', 'N']].fillna(0).assign(
                        Pts = lambda x: x.P*15 + x.G*10 - x.N*5
                        )
    team_cat_ranks['rank'] = team_cat_ranks.groupby('category')['Pts'].rank('min', ascending=False)

    st.header('Tossup data')
    st.write("Click on a team's row to show more information!")
    selection = utils.aggrid_interactive_table(team_summary)
    
    if selection["selected_rows"]:
        st.subheader(selection['selected_rows'][0]['team'])
        team_buzzes = full_buzzes[full_buzzes['team'] == selection["selected_rows"][0]['team']]
        
        st.subheader('Players')
        player_stats = team_buzzes.groupby(
            ['player', 'buzz_value']
            ).agg('size').reset_index().pivot(
            index = ['player'], columns='buzz_value', values=0
            ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        player_stats = utils.fill_out_tossup_values(player_stats).fillna(0).assign(Pts = lambda x: x.P*15 + x.G*10 - x.N*5)[['player', 'P', 'G', 'N', 'Pts']]
        player_stats[['P', 'G', 'N', 'Pts']] = player_stats[['P', 'G', 'N', 'Pts']].astype(int)
        st.dataframe(player_stats.sort_values('Pts', ascending=False))
        
        team_cats = team_buzzes.groupby(
            ['team', 'category', 'buzz_value']
            ).agg('size').reset_index().pivot(
            index = ['team', 'category'], columns='buzz_value', values=0
            ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        team_cats = utils.fill_out_tossup_values(team_cats)
                
        team_cats = team_cats[['team', 'category', 'P', 'G', 'N']].fillna(0).assign(Pts = lambda x: x.P*15 + x.G*10 - x.N*5)
        team_cats[['P', 'G', 'N', 'Pts']] = team_cats[['P', 'G', 'N', 'Pts']].astype(int).sort_values(['Pts'], ascending=False)

        st.subheader('Categories')
        col1, col2 = st.columns(2)
        team_rank = team_cats.merge(team_cat_ranks[['team', 'category', 'rank']], on=['team', 'category'])
        team_rank = team_rank[['category', 'P', 'G', 'N', 'Pts', 'rank']].rename(columns={'rank': 'Rk'})
        team_rank['Rk'] = team_rank['Rk'].astype(int)
        col1.dataframe(team_rank)
        negs = col2.checkbox("Add negs?")
        col2.altair_chart(utils.make_category_buzz_chart(team_buzzes, negs))
        
        team_subcats = team_buzzes.groupby(['category', 'subcategory', 'buzz_value']).agg(
        'size'
        ).reset_index().pivot(
            index = ['category', 'subcategory'], columns='buzz_value', values=0
            ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        team_subcats = utils.fill_out_tossup_values(team_subcats)

        team_subcats = team_subcats[['category', 'subcategory', 'P', 'G', 'N']].fillna(0).assign(Pts = lambda x: x.P*15 + x.G*10 - x.N*5)
        team_subcats[['P', 'G', 'N', 'Pts']] = team_subcats[['P', 'G', 'N', 'Pts']].astype(int).sort_values(['Pts'], ascending=False)

        col1.subheader('Subcategories')
        col1.dataframe(team_subcats)

        st.subheader('Buzzes')
        team_buzzes['packet'] = team_buzzes['packet'].astype(int)
        st.dataframe(team_buzzes[['packet', 'tossup', 'category', 'subcategory', 'answer', 'buzz_position', 'buzz_value']])



    bonus_cat = st.container()
    full_bonuses = bonuses.merge(bonus_meta[bonus_meta['season'] == 2], on=['packet', 'bonus'])
    full_bonuses['division'] = [x.split('-')[1] for x in full_bonuses['game_id']]
    
    if len(tournaments) > 0:
        full_bonuses = full_bonuses[full_bonuses['division'].isin(tournaments)]

    bonus_summary = full_bonuses.assign(
        tot = lambda x: x.part1_value + x.part2_value + x.part3_value
        ).groupby('team').agg({'tot': 'mean'}).reset_index().rename(
            columns={'tot': 'PPB'}
            ).sort_values('PPB', ascending=False)

    bonus_cat_summary = full_bonuses.assign(
        tot = lambda x: x.part1_value + x.part2_value + x.part3_value
        ).groupby(['team', 'category']).agg({'tot': 'mean'}).reset_index().rename(
            columns={'tot': 'PPB'}
            ).sort_values('PPB', ascending=False)

    bonus_summary['PPB'] = round(bonus_summary['PPB'], 2)

    with bonus_cat:
        st.header('Bonus data')
        col3, col4 = st.columns(2)
        with col3:
            selection = utils.aggrid_interactive_table(bonus_summary)

        with col4:
            if selection["selected_rows"]:
                team_bonuses = bonus_cat_summary[bonus_cat_summary['team'] == selection["selected_rows"][0]['team']]
                team_bonuses['PPB'] = round(team_bonuses['PPB'], 2)
                st.altair_chart(utils.make_category_ppb_chart(team_bonuses, bonus_cat_summary))