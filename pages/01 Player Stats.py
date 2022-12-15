import utils
import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd

for k, v in st.session_state.items():
    st.session_state[k] = v

utils.local_css("style.css")

st.title('2022 NASAT Player Stats')

st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

buzzes = utils.load_buzzes()
tossup_meta = utils.load_tossup_meta()
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
player_bpa, player_cat_bpa = utils.load_player_bpa()

player_summary = full_buzzes.groupby(
    ['player', 'team', 'value']
).agg(
    'size'
).reset_index().pivot(
    index=['player', 'team'], columns='value', values=0
).reset_index().rename(columns={10: 'G', -5: 'N'}).merge(
                        player_games, on=['player', 'team']
                        ).merge(
                            player_bpa, on = ['player', 'team']
                        ).assign(
                            BPA = lambda x: round(x.BPA, 3),
                            ACC = lambda x: round(x.ACC, 3),
                        )

player_cat_ranks = full_buzzes.groupby(['player', 'team', 'category', 'value']).agg(
    'size'
).reset_index().pivot(
    index=['player', 'team', 'category'], columns='value', values=0
).reset_index().rename(columns={10: 'G', -5: 'N'})

player_summary = utils.fill_out_tossup_values(player_summary)
player_cat_ranks = utils.fill_out_tossup_values(player_cat_ranks)

player_summary = player_summary[['player', 'team', 'Games', 'G', 'N', 'BPA', 'ACC']].fillna(0).assign(
    Pts=lambda x: x.G*10 - x.N*5
).sort_values(['Pts'], ascending=False)
player_summary['PPG'] = round(player_summary['Pts']/player_summary['Games'], 2)
player_summary = player_summary[['player', 'team', 'Games', 'G', 'N', 'Pts', 'PPG', 'BPA', 'ACC']].rename(
    columns={'G': '10', 'N': '-5', 'Games': 'G'}
)

player_cat_ranks = player_cat_ranks[['player', 'team', 'category', 'G', 'N']].fillna(0).assign(
    Pts=lambda x: x.G*10 - x.N*5
)
player_cat_ranks['rank'] = player_cat_ranks.groupby(
    'category')['Pts'].rank('min', ascending=False)

player_list, player_stats = st.columns([5, 4])
utils.hr()

with player_list:
    st.write("Click on a player's row to show more information!")
    selection = utils.aggrid_interactive_table(player_summary)

if selection["selected_rows"]:
    with player_stats:
        st.header(
            f"{selection['selected_rows'][0]['player']}, {selection['selected_rows'][0]['team']}")
        player_buzzes = full_buzzes[full_buzzes['player'] == selection["selected_rows"]
                                    [0]['player']][full_buzzes['team'] == selection["selected_rows"][0]['team']]
        player_cats = player_buzzes.groupby(
            ['player', 'team', 'category', 'value']
        ).agg('size').reset_index().pivot(
            index=['player', 'team', 'category'], columns='value', values=0
        ).reset_index().rename(columns={10: 'G', -5: 'N'})

        player_cats = utils.fill_out_tossup_values(player_cats)

        player_cats = player_cats[['player', 'team', 'category', 'G', 'N']].fillna(
            0).assign(Pts=lambda x: x.G*10 - x.N*5)
        player_cats[['G', 'N', 'Pts']] = player_cats[['G', 'N', 'Pts']].astype(
            int).sort_values(['Pts'], ascending=False)

        player_rank = player_cats.merge(player_cat_ranks[[
                                        'player', 'team', 'category', 'rank']], on=['player', 'team', 'category'])
        player_rank = player_rank[['player', 'team', 'category', 'G', 'N', 'Pts', 'rank']].rename(
            columns={'rank': 'Rk'}
            ).merge(
                player_cat_bpa, on=['player', 'team', 'category']
            )
        player_rank['Rk'] = player_rank['Rk'].astype(int)
        player_rank = player_rank[['category', 'G', 'N', 'Pts', 'Rk', 'BPA', 'ACC']].assign(
            BPA = lambda x: round(x.BPA, 3), ACC = lambda x: round(x.ACC, 3),
        )

    player_subcats = player_buzzes.groupby(['category', 'subcategory', 'value']).agg(
        'size'
    ).reset_index().pivot(
        index=['category', 'subcategory'], columns='value', values=0
    ).reset_index().rename(columns={10: 'G', -5: 'N'})

    player_subcats = utils.fill_out_tossup_values(player_subcats)

    player_subcats = player_subcats[['category', 'subcategory', 'G', 'N']].fillna(
        0).assign(Pts=lambda x: x.G*10 - x.N*5)
    player_subcats[['G', 'N', 'Pts']] = player_subcats[['G', 'N', 'Pts']].astype(
        int).sort_values(['Pts'], ascending=False)

    with player_stats:
        tab1, tab2 = st.tabs(["Categories", "Subcategories"])
    with tab1:
        utils.df_to_kable(player_rank)
    with tab2:
        utils.df_to_kable(player_subcats)

    st.header("Buzzes")
    player_buzzes['packet'] = player_buzzes['packet'].astype(int)
    packets = utils.get_packets()
    print(packets.keys())

    contexts = []
    for i, row in player_buzzes.iterrows():
        packet_sani = packets[f"packets/packet{int(row['packet'])}.json"]['tossups'][row['tossup'] -
                                                                                        1]['question'].split(' ')
        context = packet_sani[row['buzz_position']-6:row['buzz_position']]
        contexts.append(' '.join(context))

    player_buzzes['context'] = [
        context + ' | *buzz* |' for context in contexts]
    player_buzzes['answer'] = [utils.sanitize_answer(
        answer) for answer in player_buzzes['answer']]
    utils.aggrid_interactive_table(player_buzzes[['packet', 'tossup', 'category', 'subcategory', 'answer', 'buzz_position', 'value', 'context']].rename(
        columns={'buzz_position': 'word'}
    ).sort_values(['packet', 'tossup'])
    )
    utils.hr()

    st.header("Category Buzzpoint Graph")
    negs = st.checkbox("Add negs?")
    st.altair_chart(utils.make_category_buzz_chart(player_buzzes, negs))


    
