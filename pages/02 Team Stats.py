import utils
import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd

for k, v in st.session_state.items():
    st.session_state[k] = v

utils.local_css("style.css")

st.title('2022 NASAT Team Stats')

st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

buzzes = utils.load_buzzes()
bonuses = utils.load_bonuses()
tossup_meta = utils.load_tossup_meta()
bonus_meta = utils.load_bonus_meta()
packet_meta = utils.get_packet_meta()

full_buzzes = buzzes.merge(
    tossup_meta, on=['packet', 'tossup']
    ).merge(
        packet_meta, on=['packet', 'tossup']
        )

full_buzzes['celerity'] = 1 - full_buzzes['buzz_position']/full_buzzes['tossup_length']

player_stats = utils.load_player_stats()
player_games = player_stats.groupby(
    ['player', 'team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})
player_games['TUH'] = player_games['Games']*20
player_bpa, player_cat_bpa = utils.load_player_bpa()
team_bpa, team_cat_bpa = utils.load_team_bpa()
team_games = player_stats.groupby(
    ['team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})

team_summary = full_buzzes.groupby(
    ['team', 'value']
).agg(
    'size'
).reset_index().pivot(
    index=['team'], columns='value', values=0
).reset_index().rename(columns={10: 'G', -5: 'N'}).merge(
    team_bpa, on=['team']
)


team_cat_ranks = full_buzzes.groupby(['team', 'category', 'value']).agg(
    'size'
).reset_index().pivot(
    index=['team', 'category'], columns='value', values=0
).reset_index().rename(columns={10: 'G', -5: 'N'})

team_summary = utils.fill_out_tossup_values(team_summary)
team_cat_ranks = utils.fill_out_tossup_values(team_cat_ranks)

team_summary = team_summary[['team', 'G', 'N', 'BPA', 'ACC']].fillna(0).assign(
    Pts=lambda x: x.G*10 - x.N*5,
    BPA = lambda x: round(x.BPA, 3),
    ACC = lambda x: round(x.ACC, 3)
).sort_values(['Pts'], ascending=False).merge(
    team_games, on="team"
)

team_summary = team_summary[['team', 'Games', 'G', 'N', 'Pts', 'BPA', 'ACC']]

team_cat_ranks = team_cat_ranks[['team', 'category', 'G', 'N']].fillna(0).assign(
    Pts=lambda x: x.G*10 - x.N*5
)
team_cat_ranks['rank'] = team_cat_ranks.groupby(
    'category')['Pts'].rank('min', ascending=False)

team_list, team_detail = st.columns(2)
with team_list:
    st.header('Tossup data')
    st.write("Click on a team's row to show more information!")
    selection = utils.aggrid_interactive_table(team_summary)
utils.hr()

if selection["selected_rows"]:
    with team_detail:
        st.header(selection['selected_rows'][0]['team'])
        team_buzzes = full_buzzes[full_buzzes['team']
                                  == selection["selected_rows"][0]['team']]

        tab1, tab2, tab3 = st.tabs(['Players', 'Categories', 'Subcategories'])
        with tab1:
            player_stats = team_buzzes.groupby(
                ['player', 'team', 'value']
            ).agg('size').reset_index().pivot(
                index=['player', 'team'], columns='value', values=0
            ).reset_index().rename(columns={10: 'G', -5: 'N'}).merge(
                        player_games, on=['player', 'team']
                        ).merge(
                            player_bpa, on=['player', 'team']
                        )

            player_stats = utils.fill_out_tossup_values(player_stats).fillna(
                0).assign(Pts=lambda x: x.G*10 - x.N*5)[['player', 'Games', 'G', 'N', 'Pts', 'BPA', 'ACC']]
            player_stats[['G', 'N', 'Pts']] = player_stats[[
                'G', 'N', 'Pts']].astype(int)
            player_stats['PPG'] = round(player_stats['Pts']/player_stats['Games'], 2)
            player_stats['BPA'] = round(player_stats['BPA'], 3)
            player_stats['ACC'] = round(player_stats['ACC'], 3)
            player_stats = player_stats[['player', 'Games', 'G', 'N', 'Pts', 'PPG', 'BPA', 'ACC']]
            utils.df_to_kable(
                player_stats.sort_values('Pts', ascending=False))

        team_cats = team_buzzes.groupby(
            ['team', 'category', 'value']
        ).agg('size').reset_index().pivot(
            index=['team', 'category'], columns='value', values=0
        ).reset_index().rename(columns={10: 'G', -5: 'N'})

        team_cats = utils.fill_out_tossup_values(team_cats)

        team_cats = team_cats[['team', 'category', 'G', 'N']].fillna(
            0).assign(Pts=lambda x: x.G*10 - x.N*5)
        team_cats[['G', 'N', 'Pts']] = team_cats[['G', 'N', 'Pts']].astype(
            int).sort_values(['Pts'], ascending=False)
        team_rank = team_cats.merge(
            team_cat_ranks[['team', 'category', 'rank']], on=['team', 'category'])
        team_rank = team_rank[['team', 'category', 'G', 'N', 'Pts', 'rank']].rename(
            columns={'rank': 'Rk'}).merge(
                team_cat_bpa, on = ['team', 'category']
            ).assign(
                BPA = lambda x: round(x.BPA, 3),
                ACC = lambda x: round(x.ACC, 3)
            )
        team_rank['Rk'] = team_rank['Rk'].astype(int)
        team_rank = team_rank[['category', 'G', 'N', 'Pts', 'Rk', 'BPA', 'ACC']]

        with tab2:
            utils.df_to_kable(team_rank)

        team_subcats = team_buzzes.groupby(['category', 'subcategory', 'value']).agg(
            'size'
        ).reset_index().pivot(
            index=['category', 'subcategory'], columns='value', values=0
        ).reset_index().rename(columns={10: 'G', -5: 'N'})

        team_subcats = utils.fill_out_tossup_values(team_subcats)

        team_subcats = team_subcats[['category', 'subcategory', 'G', 'N']].fillna(
            0).assign(Pts=lambda x: x.G*10 - x.N*5)
        team_subcats[['G', 'N', 'Pts']] = team_subcats[['G', 'N', 'Pts']].astype(
            int).sort_values(['Pts'], ascending=False)

        with tab3:
            utils.df_to_kable(team_subcats)

    st.header("Buzzes")
    team_buzzes['packet'] = team_buzzes['packet'].astype(int)
    team_buzzes['answer'] = [utils.sanitize_answer(
        answer) for answer in team_buzzes['answer']]
    utils.aggrid_interactive_table(
        team_buzzes[['packet', 'tossup', 'category', 'subcategory',
                    'answer', 'player', 'value', 'buzz_position']]
    )
    
    st.header("Category Buzzpoints")
    negs = st.checkbox("Add negs?")
    st.altair_chart(utils.make_category_buzz_chart(team_buzzes, negs))

    utils.hr()


bonus_cat = st.container()
full_bonuses = bonuses.merge(bonus_meta, on=['packet', 'bonus'])

bonus_summary = full_bonuses.assign(
    tot=lambda x: x.part1_value + x.part2_value + x.part3_value
).groupby('team').agg({'tot': 'mean', 'part1_value': 'count'}).reset_index().rename(
    columns={'tot': 'PPB', 'part1_value': 'Bonuses'}
).sort_values('PPB', ascending=False)

bonus_cat_summary = full_bonuses.assign(
    tot=lambda x: x.part1_value + x.part2_value + x.part3_value
).groupby(['team', 'category']).agg({'tot': 'mean'}).reset_index().rename(
    columns={'tot': 'PPB'}
).sort_values('PPB', ascending=False)

bonus_summary['PPB'] = round(bonus_summary['PPB'], 2)
bonus_summary = bonus_summary[['team', 'Bonuses', 'PPB']]

col3, col4 = st.columns(2)

with bonus_cat:
    st.header('Bonus data')
    with col3:
        selection = utils.aggrid_interactive_table(bonus_summary)
    if selection["selected_rows"]:
        team_bonuses = bonus_cat_summary[bonus_cat_summary['team']
                                         == selection["selected_rows"][0]['team']]
        team_bonuses['PPB'] = round(team_bonuses['PPB'], 2)
        with col4:
            st.altair_chart(utils.make_category_ppb_chart(
                team_bonuses, bonus_cat_summary))
