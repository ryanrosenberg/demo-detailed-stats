import sqlite3 as sq
import streamlit as st
import altair as alt
import pandas as pd
import json
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

@st.experimental_memo
def make_buzz_chart(df):
    c = alt.Chart(df).mark_circle(size = 100).encode(x='buzz_position', y = alt.Y(field='num', type = 'ordinal', sort='descending'), color=alt.Color('team', legend=None), tooltip=['player', 'team', 'buzz_position', 'answer'])
    return c

@st.experimental_memo
def make_category_buzz_chart(df):
    # df['buzz_value'] = [1 if x in [15, 10] else -0.5 for x in df['buzz_value']]
    # c = alt.Chart(df).mark_bar().encode(
    #     x='buzz_position', y = alt.Y(field='buzz_value', type = 'quantitative'), color='category', tooltip=['player', 'team', 'category', 'buzz_position', 'answer']
    #         )
    df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic'] else cat for cat in df['category']]
    p = ggplot(df, aes("buzz_position")) + geom_histogram(
        aes(fill = "category"), binwidth = 10
        ) + facet_wrap(['category']) + scale_x_continuous(
            limits = [0, 140], breaks = [0, 20, 40, 60, 80, 100, 120, 140]
        ) + scale_fill_discrete(guide = False) + theme_bw() + theme(panel_border = element_blank())
    return ggplot.draw(p)

@st.experimental_memo
def make_category_ppb_chart(df, cat_ppb):
    # df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic'] else cat for cat in df['category']]
    cat_ppb['rank'] = cat_ppb.groupby('category')['PPB'].rank('min', ascending=False).astype(int)
    cat_ppb['rank'] = ['#' + str(c) for c in cat_ppb['rank']]
    print(cat_ppb[cat_ppb['team'] == df['team'].unique()[0]])
    p = ggplot() + geom_col(cat_ppb, 
        aes(x = "category", y = "PPB"), fill = 'white', color = 'black', alpha = 0
        ) + geom_col(df,
        aes( x = "category", y = "PPB", fill = "category")
        ) + geom_text(df, 
        aes(x = "category", y = "PPB", label = "PPB"), va = 'bottom'
        ) + geom_label(cat_ppb[cat_ppb['team'] == df['team'].unique()[0]], 
        aes(x = "category", y = "PPB", label = "rank"), va = 'top', nudge_y = -1
        ) + geom_tile(df,
        aes(x = 7, y = 31, width = .5, height = 2), alpha = 0, color = 'black'
        ) + annotate(geom = "text",
        x = "Science", y = 30, va = 'bottom', label = 'Top PBB'
        ) + scale_fill_cmap_d() + scale_y_continuous(
            limits = [0, 32], breaks = [0, 5, 10, 15, 20, 25, 30]
        ) + theme_bw() + theme(
            panel_border = element_blank(), axis_ticks=element_blank(), axis_text_x=element_text(angle = 45)
            )
    return ggplot.draw(p)
    
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

        options.configure_default_column(min_column_width=1)
        options.configure_selection("single")
        selection = AgGrid(
            df,
            enable_enterprise_modules=True,
            gridOptions=options.build(),
            theme="streamlit",
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