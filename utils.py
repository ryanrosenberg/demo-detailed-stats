import sqlite3 as sq

import altair as alt
import pandas as pd
from plotnine import *
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


def fetch_df(cursor):
    rows = cursor.fetchall()
    keys = [k[0] for k in cursor.description]
    game_results = [dict(zip(keys, row)) for row in rows]
    results = pd.DataFrame(game_results)
    return results

def load_data():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM buzzes')
    buzzes = fetch_df(cur)

    cur.execute('SELECT * FROM bonuses')
    bonuses = fetch_df(cur)

    cur.execute('SELECT * FROM tossup_meta')
    tossup_meta = fetch_df(cur)

    return buzzes, bonuses, tossup_meta

def make_buzz_chart(df):
    c = alt.Chart(df).mark_circle(size = 100).encode(x='buzz_position', y = alt.Y(field='num', type = 'ordinal', sort='descending'), color='team', tooltip=['player', 'team', 'buzz_position', 'answer'])
    return c

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

def make_subcategory_buzz_chart(df):
    # df['buzz_value'] = [1 if x in [15, 10] else -0.5 for x in df['buzz_value']]
    # c = alt.Chart(df).mark_bar().encode(
    #     x='buzz_position', y = alt.Y(field='buzz_value', type = 'quantitative'), color='category', tooltip=['player', 'team', 'category', 'buzz_position', 'answer']
    #         )
    p = ggplot(df, aes("buzz_position")) + geom_density(aes(fill = "subcategory"), alpha = .5) + scale_x_continuous(limits = [0, 150]) + theme_bw() + theme(panel_border = element_blank())
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

def fill_out_tossup_values(df):
    tossup_values = ['P', 'G', 'N']
    for entry in tossup_values:
            if entry not in list(df):
                df[entry] = 0
    return df