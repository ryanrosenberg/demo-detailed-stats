import streamlit as st
import pandas as pd
import sqlite3 as sq
import altair as alt
import utils

def app(tournaments):
    st.title('QB League Season 2 -- Categories')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)

    st.subheader('Category data')

    buzzes = utils.load_buzzes()
    tossup_meta = utils.load_tossup_meta()

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == 2], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]
    
    if len(tournaments) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(tournaments)]

    cats = full_buzzes['category'].unique()
    cats.sort()
    filter_categories = st.multiselect('Categories', cats, default=[])

    tossup_cat = st.container()
    with tossup_cat:
        col1, col2 = st.columns(2)
        if len(filter_categories) > 0:
            filter_buzzes = full_buzzes[full_buzzes['category'].isin(filter_categories)]
            subcats = filter_buzzes['subcategory'].unique()
            filter_subcategories = st.multiselect('Subcategories', subcats, default=subcats)
            chart_buzzes = filter_buzzes[filter_buzzes['subcategory'].isin(filter_subcategories)]
            chart_buzzes['num'] = chart_buzzes.groupby(['buzz_position']).cumcount()+1
            category_summary = chart_buzzes.groupby(
                ['player', 'team', 'buzz_value']
                ).agg(
                    'size'
                    ).reset_index().pivot(
                        index = ['player', 'team'], columns='buzz_value', values=0
                        ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})

        else:
            chart_buzzes = full_buzzes
            chart_buzzes['num'] = full_buzzes.groupby(['buzz_position']).cumcount()+1
            category_summary = full_buzzes.groupby(
                ['player', 'team', 'buzz_value']
                ).agg(
                    'size'
                    ).reset_index().pivot(
                        index = ['player', 'team'], columns='buzz_value', values=0
                        ).reset_index().rename(columns={15: 'P', 10: 'G', -5:'N'})
                        
        player_stats = category_summary[['player', 'team', 'P', 'G', 'N']].fillna(0).assign(
            Pts = lambda x: x.P*15 + x.G*10 - x.N*5
            ).sort_values(('Pts'), ascending=False)

        player_stats[['P', 'G', 'N', 'Pts']] = player_stats[['P', 'G', 'N', 'Pts']].astype(int)

        with col1:
            selected = utils.aggrid_interactive_table(player_stats)
        with col2:
            c = utils.make_buzz_chart(chart_buzzes)
            st.altair_chart(c, use_container_width=True)