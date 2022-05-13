import json
from pickle import FALSE
import sqlite3 as sq
from textwrap import wrap

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st
from altair import datum
from plotnine import *
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


def fetch_df(_cursor):
    rows = _cursor.fetchall()
    keys = [k[0] for k in _cursor.description]
    game_results = [dict(zip(keys, row)) for row in rows]
    results = pd.DataFrame(game_results)
    return results

@st.cache
def load_buzzes():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM buzzes')
    buzzes = fetch_df(cur)
    con.close()
    return buzzes

@st.cache
def load_bonuses():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM bonuses')
    bonuses = fetch_df(cur)
    con.close()
    return bonuses

@st.cache
def load_tossup_meta():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM tossup_meta')
    tossup_meta = fetch_df(cur)
    con.close()
    return tossup_meta

@st.cache
def load_bonus_meta():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM bonus_meta')
    bonus_meta = fetch_df(cur)
    con.close()
    return bonus_meta

@st.cache
def load_team_stats():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM team_stats')
    team_stats = fetch_df(cur)
    con.close()
    return team_stats

@st.cache
def load_player_stats():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM player_stats')
    player_stats = fetch_df(cur)
    con.close()
    return player_stats

@st.experimental_memo
def make_buzz_chart(df):
    c = alt.Chart(df).mark_square(size = 100).encode(x='buzz_position', y = alt.Y(field='num', type = 'ordinal', sort='descending'), color=alt.Color('team', legend=None), tooltip=['player', 'team', 'buzz_position', 'answer'])
    return c

@st.experimental_memo
def make_category_buzz_chart(df, negs):
    df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic'] else cat for cat in df['category']]
    if not negs:
        df = df[df['buzz_value'].isin([15, 10])]
    # p = ggplot(df, aes("buzz_position")) + geom_histogram(
    #     aes(fill = "category"), binwidth = 10
    #     ) + facet_wrap(['category']) + scale_x_continuous(
    #         limits = [0, 140], breaks = [0, 20, 40, 60, 80, 100, 120, 140]
    #     ) + scale_fill_discrete(guide = False) + theme_bw() + theme(panel_border = element_blank())
    c = alt.Chart(df).mark_bar(
    opacity=0.8,
    binSpacing=2
    ).encode(
        x= alt.X('buzz_position', bin=alt.Bin(maxbins=10),
        scale=alt.Scale(domain=(0, 150))),
        y = alt.Y('count()', stack=None), 
        color='category', 
        facet = alt.Facet('category', columns=2)
    ).properties(
    width=200,
    height=150,
)
    return c

@st.experimental_memo
def make_category_ppb_chart(df, cat_ppb):
    # df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic'] else cat for cat in df['category']]
    cat_ppb['rank'] = cat_ppb.groupby('category')['PPB'].rank('min', ascending=False).astype(int)
    top_ppb = cat_ppb[cat_ppb['rank'] == 1]
    cat_ppb['rank'] = ['#' + str(c) for c in cat_ppb['rank']]
    cat_ppb = cat_ppb[cat_ppb['team'] == df['team'].unique()[0]]
    # print(cat_ppb[cat_ppb['team'] == df['team'].unique()[0]])
    # p = ggplot() + geom_col(cat_ppb, 
    #     aes(x = "category", y = "PPB"), fill = 'white', color = 'black', alpha = 0
    #     ) + geom_col(df,
    #     aes( x = "category", y = "PPB", fill = "category")
    #     ) + geom_text(df, 
    #     aes(x = "category", y = "PPB", label = "PPB"), va = 'bottom'
    #     ) + geom_label(cat_ppb[cat_ppb['team'] == df['team'].unique()[0]], 
    #     aes(x = "category", y = "PPB", label = "rank"), va = 'top', nudge_y = -1
    #     ) + geom_tile(df,
    #     aes(x = 7, y = 31, width = .5, height = 2), alpha = 0, color = 'black'
    #     ) + annotate(geom = "text",
    #     x = "Science", y = 30, va = 'bottom', label = 'Top PBB'
    #     ) + scale_fill_cmap_d() + scale_y_continuous(
    #         limits = [0, 32], breaks = [0, 5, 10, 15, 20, 25, 30]
    #     ) + theme_bw() + theme(
    #         panel_border = element_blank(), axis_ticks=element_blank(), axis_text_x=element_text(angle = 45)
    #         )
    # return ggplot.draw(p)

    bar = alt.Chart(df).mark_bar().encode(
    x='category',
    y='PPB',
    color = alt.Color('category', scale=alt.Scale(scheme='viridis'))
    ).properties(
        width=alt.Step(60),  # controls width of bar.
        height = 350
    )

    top = alt.Chart(top_ppb).mark_bar(
        color='black',
        opacity = 0.15,
        thickness=2,
        size=60 * 0.9,  # controls width of tick.
    ).encode(
        x='category',
        y='PPB'
    )

    ppb = alt.Chart(df).mark_text(
        color='black',
        size = 14,
        dy = -3,
        baseline='bottom'
    ).encode(
        x='category',
        y='PPB',
        text = 'PPB'
    )

    rank = alt.Chart(cat_ppb).mark_text(
        color='white',
        fontWeight='bold',
        size = 14,
        dy = 5,
        baseline='top'
    ).encode(
        x='category',
        y='PPB',
        text = 'rank'
    )

    return bar + top + ppb + rank
    
def aggrid_interactive_table(df: pd.DataFrame):
        """Creates an st-aggrid interactive table based on a dataframe.
        Args:
            df (pd.DataFrame]): Source dataframe
        Returns:
            dict: The selected row
        """
        options = GridOptionsBuilder.from_dataframe(
            df, enableValue=True
        )

        options.configure_default_column(min_column_width=0.1)
        options.configure_selection("single")

        for name in df.columns:
            if name in ['P', 'G', 'N']:
                options.configure_column(name, width = 1)

        custom_css = {
            ".ag-header-viewport": {"background-color": "white"},
            ".ag-theme-streamlit .ag-root-wrapper": {"border": "0px solid pink !important"},
            ".ag-theme-streamlit .ag-header" : {"border": "0px solid pink !important"},
            ".ag-header-cell" : {
                "background-color": "#555555", "color": "white",
                "border-bottom": "4px solid #ff4b4b !important"}
        }
        selection = AgGrid(
            df,
            enable_enterprise_modules=True,
            gridOptions=options.build(),
            theme="streamlit",
            custom_css=custom_css,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
        )

        return selection

@st.experimental_memo
def fill_out_tossup_values(df):
    tossup_values = ['P', 'G', 'N']
    for entry in tossup_values:
            if entry not in list(df):
                df[entry] = 0
    return df

@st.experimental_memo
def get_packets():
    packets = []
    for i in range(1, 10):
        with open(f'packets/packet{str(i)}.json', 'r') as f:
            packets.append(json.load(f))
    return packets

def make_scoresheet(game_id, buzzes, bonuses, player_stats):
    game_buzzes = buzzes[buzzes['game_id'] == game_id]
    game_bonuses = bonuses[bonuses['game_id'] == game_id]

    game_buzzes['buzz_value'] = game_buzzes['buzz_value'].astype(int)

    # scoresheet = game_buzzes.pivot(
    #     index = ['tossup'], columns=['team','player'], values='buzz_value'
    # ).reset_index().fillna(0).astype(int).astype(str).replace('0', '').reset_index()

    # scoresheet.columns = scoresheet.columns.str.replace(' ', '\n')

    # team_tossups = []
    # for team in player_stats['team']:
    #     player_tossups = []
    #     for player in player_stats[player_stats['team'] == team]['player']:
    #         player_game = [None]*21
    #         for i, row in buzzes[buzzes['team'] == team][buzzes['player'] == player].iterrows():
    #             player_game[row['tossup']] = row['buzz_value']
    #         player_tossups.append({'player': player, 'tossups': player_game})
    # print(team_tossups)
    team1_name = game_buzzes['team'].unique().tolist()[0]
    team2_name = game_buzzes['team'].unique().tolist()[1]

    team1_buzzes = game_buzzes[game_buzzes['team'] == team1_name]
    team2_buzzes = game_buzzes[game_buzzes['team'] == team2_name]

    team1_bonuses = game_bonuses[game_bonuses['team'] == team1_name]
    team2_bonuses = game_bonuses[game_bonuses['team'] == team2_name]

    team1_bonuses = team1_bonuses.melt(
        id_vars = ['tossup', 'answers'],
        value_vars = ['part1_value', 'part2_value', 'part3_value'],
        var_name='part', value_name='value'
    )

    team2_bonuses = team2_bonuses.melt(
        id_vars = ['tossup', 'answers'],
        value_vars = ['part1_value', 'part2_value', 'part3_value'],
        var_name='part', value_name='value'
    )

    team1_score = []
    team2_score = []
    rscore1 = 0
    rscore2 = 0
    for i in range(1,21):
        if len(team1_buzzes[team1_buzzes['tossup'] == i]['buzz_value']) > 0:
            team1_tossup = sum(team1_buzzes[team1_buzzes['tossup'] == i]['buzz_value'].tolist())
            team1_bonus = sum(team1_bonuses[team1_bonuses['tossup'] == i]['value'].tolist())
            team1_score.append(rscore1 + team1_tossup + team1_bonus)
            rscore1 = rscore1 + team1_tossup + team1_bonus
        else:
            team1_score.append(rscore1)
        
        if len(team2_buzzes[team2_buzzes['tossup'] == i]['buzz_value']) > 0:
            team2_tossup = sum(team2_buzzes[team2_buzzes['tossup'] == i]['buzz_value'].tolist())
            team2_bonus = sum(team2_bonuses[team2_bonuses['tossup'] == i]['value'].tolist())
            team2_score.append(rscore2 + team2_tossup + team2_bonus)
            rscore2 = rscore2 + team2_tossup + team2_bonus
        else:
            team2_score.append(rscore2)

    team1_score_df = pd.DataFrame({'tossup': list(range(1,21)), 'score': team1_score, 'total': [1]*20})
    team2_score_df = pd.DataFrame({'tossup': list(range(1,21)), 'score': team2_score, 'total': [1]*20})

    all_player_cells = pd.DataFrame({
        'player': np.repeat(player_stats['player'].unique(), 20),
        'tossup': list(range(1, 21))*len(player_stats['player'].unique())
        })

    all_bonus_cells = pd.DataFrame({
        'part': np.repeat(['part1_value', 'part2_value', 'part3_value'], 20),
        'tossup': list(range(1, 21))*3
        })
    
    all_total_cells = pd.DataFrame({
        'total': np.repeat(1, 20),
        'tossup': list(range(1, 21))
        })

    t1_tossups = alt.Chart(team1_buzzes).mark_text(
        ).encode(
        x = alt.X(
            "player:N", 
            axis = alt.Axis(orient='top', ticks = False, offset=5),
            scale = alt.Scale(domain = player_stats[player_stats['team'] == team1_name]['player'].unique()),
            title = None),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = alt.Axis(
                orient='left', grid = False, ticks = False, tickCount= 20, title=None, labelAlign='right', labelFontWeight='bold', labelAngle=0
            )),
        text = 'buzz_value:Q',
        tooltip = [alt.Tooltip('answer:N', title="Tossup answer"), alt.Tooltip('buzz_position:Q', title="Buzz location")])
    t1_bonuses = alt.Chart(team1_bonuses).mark_text().encode(
        x = alt.X(
            'part:N', 
            axis = alt.Axis(orient = 'top', ticks = False, labels = False, offset=5, title = wrap(team1_name, width=12))
            ),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = None),
        text = 'value:Q',
        tooltip = [alt.Tooltip('answers:N', title="Bonus answers")])
    t1_score = alt.Chart(team1_score_df).mark_text().encode(
        x = alt.X('total:N', axis = alt.Axis(orient='top', ticks = False, labels = False, offset=5)),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = None),
        text = 'score:Q')
    t2_tossups = alt.Chart(team2_buzzes).mark_text().encode(
        x = alt.X(
            "player:N", 
            axis = alt.Axis(orient='top', ticks = False, offset=5),
            scale = alt.Scale(domain = player_stats[player_stats['team'] == team2_name]['player'].unique()),
            title = None),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = alt.Axis(
                orient='left', grid = False, ticks = False, tickCount= 20, title=None, labelAlign='right', labelFontWeight='bold', labelAngle=0
            )),
        text = 'buzz_value:Q',
        tooltip = [alt.Tooltip('answer:N', title="Tossup answer"), alt.Tooltip('buzz_position:Q', title="Buzz location")])
    t2_bonuses = alt.Chart(team2_bonuses).mark_text().encode(
        x = alt.X(
            'part:N', 
            axis = alt.Axis(orient = 'top', ticks = False, labels = False, offset=5, title = wrap(team2_name, width=12))
            ),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = None),
        text = 'value:Q',
        tooltip = [alt.Tooltip('answers:N', title="Bonus answers")])
    t2_score = alt.Chart(team2_score_df).mark_text().encode(
        x = alt.X('total:N', axis = alt.Axis(orient='top', ticks = False, offset=5, labels = False)),
        y = alt.Y(
            'tossup:O', 
            scale = alt.Scale(domain=list(range(1,21))),
            axis = None),
        text = 'score:Q')

    player_grid = alt.Chart(all_player_cells).mark_rect(
        stroke = 'black', strokeWidth=.1, fill = None
        ).encode(
        x = 'player:N', y = 'tossup:O'
    )

    bonus_grid = alt.Chart(all_bonus_cells).mark_rect(
        stroke = 'black', strokeWidth=.1, fill = None
        ).encode(
        x = 'part:N', y = 'tossup:O'
    )

    total_grid = alt.Chart(all_total_cells).mark_rect(
        stroke = 'black', strokeWidth=.1, fill = None
        ).encode(
        x = 'total:N', y = 'tossup:O'
    )

    return alt.hconcat(
        alt.hconcat(t1_tossups + player_grid, t1_bonuses + bonus_grid, t1_score + total_grid, spacing = -5), 
        alt.hconcat(t2_tossups + player_grid, t2_bonuses + bonus_grid, t2_score + total_grid, spacing = -5), 
        spacing = -20).configure(
            font = 'Segoe UI'
        ).configure_axis(labelAngle = 45).configure_text(size = 11)
    # return team1_buzzes
