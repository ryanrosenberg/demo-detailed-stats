import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import sqlite3 as sq
import altair as alt

st.title('QB League Season 2 Divison 1')

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

    cur.execute('SELECT * FROM tossup_meta')
    tossup_meta = fetch_df(cur)

    return buzzes, tossup_meta

def make_buzz_chart(df):
    c = alt.Chart(df).mark_circle(size = 100).encode(x='buzz_position', y = alt.Y(field='num', type = 'ordinal', sort='descending'), color='team', tooltip=['player', 'team', 'buzz_position', 'answer'])
    return c

st.subheader('Category data')

buzzes, tossup_meta = load_data()
full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
cats = full_buzzes['category'].unique()
cats.sort()
filter_categories = st.multiselect('Categories', cats, default=[])

if len(filter_categories) > 0:
    filter_buzzes = full_buzzes[full_buzzes['category'].isin(filter_categories)]
    subcats = filter_buzzes['subcategory'].unique()
    filter_subcategories = st.multiselect('Subcategories', subcats, default=subcats)
    subfilter_buzzes = filter_buzzes[filter_buzzes['subcategory'].isin(filter_subcategories)]
    subfilter_buzzes['num'] = subfilter_buzzes.groupby(['buzz_position']).cumcount()+1
    category_summary = subfilter_buzzes.groupby(
        ['player', 'team', 'buzz_value']
        ).agg(
            'size'
            ).reset_index().pivot(
                index = ['player', 'team'], columns='buzz_value', values=0
                ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    c = make_buzz_chart(subfilter_buzzes)
else:
    full_buzzes['num'] = full_buzzes.groupby(['buzz_position']).cumcount()+1
    category_summary = full_buzzes.groupby(
        ['player', 'team', 'buzz_value']
        ).agg(
            'size'
            ).reset_index().pivot(
                index = ['player', 'team'], columns='buzz_value', values=0
                ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

    c = make_buzz_chart(full_buzzes)
                
player_stats = category_summary[['player', 'team', 'P', 'G', 'N']].fillna(0).assign(
    Pts = lambda x: x.P*15 + x.G*10 - x.N*5
    ).sort_values(('Pts'), ascending=False)

player_stats[['P', 'G', 'N', 'Pts']] = player_stats[['P', 'G', 'N', 'Pts']].astype(int)

col1, col2 = st.columns(2)
with col1:
    st.write(player_stats)
with col2:
    st.altair_chart(c, use_container_width=True)

