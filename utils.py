import json
from pickle import FALSE
import sqlite3 as sq
import re
import glob
from textwrap import wrap

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st
from altair import datum
from plotnine import *
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid.shared import GridUpdateMode
import subprocess

def fetch_df(_cursor):
    rows = _cursor.fetchall()
    keys = [k[0] for k in _cursor.description]
    game_results = [dict(zip(keys, row)) for row in rows]
    results = pd.DataFrame(game_results)
    return results

def parse_stats(qbj):
    match_players = []
    for team in qbj['match_teams']:
        for lineup in team['lineups']:
            match_players.extend(
                [{'name': player['name'], 'team': team['team']['name']} for player in lineup['players']])

    buzzes = []
    for question in qbj['match_questions']:
        for buzz in question['buzzes']:
            buzzes.append(
                {
                    'tossup': question['question_number'],
                    'player': buzz['player']['name'],
                    'team': buzz['team']['name'],
                    'buzz_position': buzz['buzz_position']['word_index'],
                    'value': str(buzz['result']['value'])
                }
            )
    player_stats = pd.DataFrame(buzzes).groupby(
        ['player', 'team', 'value'], as_index=False
    ).agg('size').pivot(
        index=['player', 'team'], columns='value', values='size'
    ).reset_index()

    for x in ['10', '-5']:
        if x not in player_stats.columns:
            player_stats[x] = 0

    if '0' in player_stats.columns:
        player_stats = player_stats.drop(columns=['0'])

    for player in match_players:
        if player['name'] not in player_stats['player'].values:
            player_stats.loc[len(player_stats.index)] = [
                player['name'], player['team'], 0, 0]

    player_stats[['10', '-5']] = player_stats[['10', '-5']].fillna(0).astype(int)
    player_stats['Pts'] = 10*player_stats['10'] - 5*player_stats['-5']
    player_stats = player_stats[['player', 'team', '10', '-5', 'Pts']]

    buzzes = pd.DataFrame(buzzes)

    all_bonuses = [{'bonus': question['bonus'], 'question_number': question['question_number']} for question in qbj['match_questions'] if 'bonus' in question]
    bonus_df = []
    bonuses = []
    for bonus in all_bonuses:
        bonus_df.append(
            {
                'tossup': bonus['question_number'],
                'bonus': bonus['bonus']['question']['question_number'],
                'value': sum([part['controlled_points'] for part in bonus['bonus']['parts']])
            }
        )

        bonuses.append(
            {
                'tossup': bonus['question_number'],
                'bonus': bonus['bonus']['question']['question_number'],
                'part1_value': bonus['bonus']['parts'][0]['controlled_points'],
                'part2_value': bonus['bonus']['parts'][1]['controlled_points'],
                'part3_value': bonus['bonus']['parts'][2]['controlled_points']
            }
        )

    team_bonuses = pd.DataFrame(bonus_df).merge(buzzes[buzzes['value'] == '10'][['tossup', 'team']], on = 'tossup').groupby(['team'], as_index=False).agg(
        {'value': 'sum'}
    ).rename(columns={'value': 'BPts'})

    bonuses = pd.DataFrame(bonuses).merge(buzzes[buzzes['value'] == '10'][['tossup', 'team']], on = 'tossup')

    team_stats = player_stats.groupby('team', as_index=False).agg('sum').rename(columns={'Pts': 'TUPts'})
    team_stats['BHrd'] = team_stats['10']
    team_stats = team_stats.merge(pd.DataFrame(team_bonuses))
    team_stats['PPB'] = team_stats['BPts']/team_stats['BHrd']
    team_stats['PPB'] = team_stats['PPB'].round(decimals=2)
    team_stats['Pts'] = team_stats['TUPts'] + team_stats['BPts']

    for team in qbj['match_teams']:
        if team['team']['name'] not in team_stats['team'].values:
            team_stats.loc[len(team_stats.index)] = [
                team['team']['name'], 0, 0, 0, 0, 0, 0.00, 0]

    return buzzes, bonuses, player_stats, team_stats

def parse_packet(packet):
    tossup_meta = []
    for i in range(len(packet['tossups'])):
        print(i)
        if 'metadata' in packet['tossups'][i]:
            tossup_meta.append(
                {
                    'tossup': i + 1,
                    'answer': packet['tossups'][i]['answer'],
                    'author': packet['tossups'][i]['metadata'].split(', ')[0],
                    'category': packet['tossups'][i]['metadata'].split(', ')[1]
                }
            )
        else:
            tossup_meta.append(
                {
                    'tossup': i + 1,
                    'answer': packet['tossups'][i]['answer'],
                    'category': packet['tossups'][i]['category'],
                    'subcategory': packet['tossups'][i]['subcategory']
                }
            )

    tossup_meta = pd.DataFrame(tossup_meta)

    bonus_meta = []
    for i in range(len(packet['bonuses'])):
        if 'metadata' in packet['bonuses'][i]:
            bonus_meta.append(
                {
                    'bonus': i + 1,
                    'answers': ' / '.join(packet['bonuses'][i]['answers_sanitized']),
                    'author': packet['bonuses'][i]['metadata'].split(', ')[0],
                    'category': packet['bonuses'][i]['metadata'].split(', ')[1]
                }
            )
        else:
            bonus_meta.append(
                {
                    'bonus': i + 1,
                    'answers': ' / '.join(packet['bonuses'][i]['formatted_answers']),
                    'category': packet['bonuses'][i]['category'],
                    'subcategory': packet['bonuses'][i]['subcategory']
                }
            )

    bonus_meta = pd.DataFrame(bonus_meta)

    return tossup_meta, bonus_meta

def populate_db_qbjs(qbjs):
    all_buzzes = []
    all_bonuses = []
    all_player_stats = []
    all_team_stats = []

    for i, qbj_path in enumerate(qbjs):
        qbj = json.load(qbj_path)
        print(qbj_path.name)
        packet = re.search(r'(?<=Round\s)\d+', qbj_path.name).group(0)
        buzzes, bonuses, player_stats, team_stats = parse_stats(qbj)

        buzzes['packet'] = packet
        buzzes['game_id'] = i
        bonuses['packet'] = packet
        bonuses['game_id'] = i
        player_stats['packet'] = packet
        player_stats['game_id'] = i
        team_stats['packet'] = packet
        team_stats['game_id'] = i

        all_buzzes.append(buzzes)
        all_bonuses.append(bonuses)
        all_player_stats.append(player_stats)
        all_team_stats.append(team_stats)

    player_bpas, player_cat_bpas = calculate_player_bpas(pd.concat(all_buzzes), pd.concat(all_player_stats))
    team_bpas, team_cat_bpas = calculate_team_bpas(pd.concat(all_buzzes), pd.concat(all_player_stats))

    con = sq.connect('stats.db')

    pd.concat(all_buzzes).to_sql(name='buzzes', con=con, if_exists='replace')
    pd.concat(all_bonuses).to_sql(name='bonuses', con=con, if_exists='replace')
    pd.concat(all_player_stats).to_sql(name='player_stats', con=con, if_exists='replace')
    pd.concat(all_team_stats).to_sql(name='team_stats', con=con, if_exists='replace')

    print(player_bpas)
    player_bpas.to_sql(name = 'player_bpa', con=con, if_exists='replace')
    player_cat_bpas.to_sql(name = 'player_cat_bpa', con=con, if_exists='replace')
    team_bpas.to_sql(name = 'team_bpa', con=con, if_exists='replace')
    team_cat_bpas.to_sql(name = 'team_cat_bpa', con=con, if_exists='replace')

def populate_db_qbjs_nasat():
    all_buzzes = []
    all_bonuses = []
    all_player_stats = []
    all_team_stats = []

    for i, qbj_path in enumerate(glob.glob('qbjs/*.qbj')):
        with open(qbj_path, 'r') as f:
            qbj = json.load(f)

        packet = re.search(r'(?<=Round\s)\d+', qbj_path).group(0)
        buzzes, bonuses, player_stats, team_stats = parse_stats(qbj)

        buzzes['packet'] = packet
        buzzes['game_id'] = i
        bonuses['packet'] = packet
        bonuses['game_id'] = i
        player_stats['packet'] = packet
        player_stats['game_id'] = i
        team_stats['packet'] = packet
        team_stats['game_id'] = i

        all_buzzes.append(buzzes)
        all_bonuses.append(bonuses)
        all_player_stats.append(player_stats)
        all_team_stats.append(team_stats)

    player_bpas, player_cat_bpas = calculate_player_bpas(pd.concat(all_buzzes), pd.concat(all_player_stats))
    team_bpas, team_cat_bpas = calculate_team_bpas(pd.concat(all_buzzes), pd.concat(all_player_stats))

    con = sq.connect('stats.db')

    pd.concat(all_buzzes).to_sql(name='buzzes', con=con, if_exists='replace')
    pd.concat(all_bonuses).to_sql(name='bonuses', con=con, if_exists='replace')
    pd.concat(all_player_stats).to_sql(name='player_stats', con=con, if_exists='replace')
    pd.concat(all_team_stats).to_sql(name='team_stats', con=con, if_exists='replace')

    print(player_bpas)
    player_bpas.to_sql(name = 'player_bpa', con=con, if_exists='replace')
    player_cat_bpas.to_sql(name = 'player_cat_bpa', con=con, if_exists='replace')
    team_bpas.to_sql(name = 'team_bpa', con=con, if_exists='replace')
    team_cat_bpas.to_sql(name = 'team_cat_bpa', con=con, if_exists='replace')
def populate_db_packets(packets):
    all_tossup_meta = []
    all_bonus_meta = []
    for packet_path in packets:
        packet = json.load(packet_path)
        packet_num = re.search(r'(?<=packet)\d+', packet_path.name).group(0)

        json_object = json.dumps(packet)

        with open(f"packets/packet{packet_num}.json", "w") as outfile:
            outfile.write(json_object)

        tossup_meta, bonus_meta = parse_packet(packet)
        tossup_meta['packet'] = packet_num
        bonus_meta['packet'] = packet_num
        all_tossup_meta.append(tossup_meta)
        all_bonus_meta.append(bonus_meta)

    con = sq.connect('stats.db')

    pd.concat(all_tossup_meta).to_sql(name='tossup_meta', con=con, if_exists='replace')
    pd.concat(all_bonus_meta).to_sql(name='bonus_meta', con=con, if_exists='replace')

def populate_db_packets_nasat():
    all_tossup_meta = []
    all_bonus_meta = []
    for packet_path in glob.glob('packets/*.json'):
        with open(packet_path, "r") as f:
            packet = json.load(f)

        packet_num = re.search(r'(?<=packet)\d+', packet_path).group(0)

        print(packet_path)
        tossup_meta, bonus_meta = parse_packet(packet)

        tossup_meta['packet'] = packet_num
        bonus_meta['packet'] = packet_num
        all_tossup_meta.append(tossup_meta)
        all_bonus_meta.append(bonus_meta)

    con = sq.connect('stats.db')
    
    pd.concat(all_tossup_meta).to_sql(name='tossup_meta', con=con, if_exists='replace')
    pd.concat(all_bonus_meta).to_sql(name='bonus_meta', con=con, if_exists='replace')

def load_buzzes():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM buzzes')
    buzzes = fetch_df(cur)
    con.close()
    buzzes[['packet']] = buzzes[['packet']].astype(int)
    buzzes[['tossup']] = buzzes[['tossup']].astype(int)
    buzzes[['buzz_position']] = buzzes[['buzz_position']].astype(int)
    buzzes[['value']] = buzzes[['value']].astype(int)
    return buzzes


def load_bonuses():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM bonuses')
    bonuses = fetch_df(cur)
    con.close()
    bonuses[['packet']] = bonuses[['packet']].astype(int)
    bonuses[['bonus']] = bonuses[['bonus']].astype(int)
    bonuses[['tossup']] = bonuses[['tossup']].astype(int)
    return bonuses

def load_tossup_meta():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM tossup_meta')
    tossup_meta = fetch_df(cur)
    con.close()
    tossup_meta[['packet']] = tossup_meta[['packet']].astype(int)
    return tossup_meta

def load_bonus_meta():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM bonus_meta')
    bonus_meta = fetch_df(cur)
    con.close()
    bonus_meta[['packet']] = bonus_meta[['packet']].astype(int)
    return bonus_meta

def load_team_stats():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM team_stats')
    team_stats = fetch_df(cur)
    con.close()
    return team_stats


def load_player_stats():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM player_stats')
    player_stats = fetch_df(cur)
    con.close()
    return player_stats

def load_player_bpa():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM player_bpa')
    player_bpa = fetch_df(cur)
    cur.execute('SELECT * FROM player_cat_bpa')
    player_cat_bpa = fetch_df(cur)
    con.close()
    return player_bpa, player_cat_bpa

def load_team_bpa():
    con = sq.connect('stats.db')
    cur = con.cursor()

    cur.execute('SELECT * FROM team_bpa')
    team_bpa = fetch_df(cur)
    cur.execute('SELECT * FROM team_cat_bpa')
    team_cat_bpa = fetch_df(cur)
    con.close()
    return team_bpa, team_cat_bpa
    

def make_buzz_chart(df):
    c = alt.Chart(df).mark_square(size=100).encode(x='buzz_position', y=alt.Y(field='num', type='ordinal',
                                                                              sort='descending'), color=alt.Color('team', legend=None), tooltip=['player', 'team', 'buzz_position', 'answer'])
    return c


def make_category_buzz_chart(df, negs):
    df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic']
                      else cat for cat in df['category']]
    if not negs:
        df = df[df['value'].isin([15, 10])]
    else:
        df = df[df['value'].isin([15, 10, -5])]

    
    domain = [15, 10, -5]
    range_ = ['blue', '#007ccf', '#ff4b4b']
    # p = ggplot(df, aes("buzz_position")) + geom_histogram(
    #     aes(fill = "category"), binwidth = 10
    #     ) + facet_wrap(['category']) + scale_x_continuous(
    #         limits = [0, 140], breaks = [0, 20, 40, 60, 80, 100, 120, 140]
    #     ) + scale_fill_discrete(guide = False) + theme_bw() + theme(panel_border = element_blank())
    c = alt.Chart(df).mark_bar(
        opacity=0.8,
        binSpacing=2
    ).encode(
        x=alt.X('buzz_position', bin=alt.Bin(maxbins=10),
                scale=alt.Scale(domain=(0, 150))),
        y=alt.Y('count()'),
        color=alt.Color('value:O', scale=alt.Scale(domain=domain, range = range_)),
        facet=alt.Facet('category', columns=2)
    ).properties(
        width=200,
        height=150,
    )
    return c


@st.experimental_memo
def make_category_ppb_chart(df, cat_ppb):
    # df['category'] = ['Other' if cat in ['Geo/CE', 'Other Academic'] else cat for cat in df['category']]
    cat_ppb['rank'] = cat_ppb.groupby('category')['PPB'].rank(
        'min', ascending=False).astype(int)
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
        y=alt.Y('PPB', scale = alt.Scale(domain = [0, 30])),
        color=alt.Color('category', scale=alt.Scale(scheme='viridis'))
    ).properties(
        width=alt.Step(60),  # controls width of bar.
        height=350
    )

    top = alt.Chart(top_ppb).mark_bar(
        color='black',
        opacity=0.15,
        thickness=2,
        size=60 * 0.9,  # controls width of tick.
    ).encode(
        x='category',
        y='PPB'
    )

    ppb = alt.Chart(df).mark_text(
        color='black',
        size=14,
        dy=-3,
        baseline='bottom'
    ).encode(
        x='category',
        y='PPB',
        text='PPB'
    )

    rank = alt.Chart(cat_ppb).mark_text(
        color='white',
        fontWeight='bold',
        size=14,
        dy=5,
        baseline='top'
    ).encode(
        x='category',
        y='PPB',
        text='rank'
    )

    return bar + top + ppb + rank

def local_css(file_name):
    st.markdown('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inconsolata&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    st.markdown('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" />', unsafe_allow_html=True)
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def sanitize_answer(answer):
    answer = re.sub(r'\<b\>', '', answer)
    answer = re.sub(r'\<i\>', '', answer)
    answer = re.sub(r'\</b\>', '', answer)
    answer = re.sub(r'\</i\>', '', answer)
    answer = re.sub(r'\</u\>', '', answer)
    answer = re.sub(r'\<u\>', '', answer)
    answer = re.sub(r'\<em\>', '', answer)
    answer = re.sub(r'\</em\>', '', answer)
    answer = re.sub(r'\s\[.*', '', answer)

    return answer

def hr():
    return st.markdown('<hr>', unsafe_allow_html=True)

def aggrid_interactive_table(df: pd.DataFrame, accent_color='#ff4b4b', height=400):
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
    options.configure_pagination()
    # options.configure_auto_height(False)

    for name in df.columns:
        if name in ['P', 'G', 'N']:
            options.configure_column(name, width=1)

    custom_css = {
        ".ag-header-viewport": {"background-color": "white"},
        ".ag-paging-panel": {"font-size": "1.2em"},
        ".ag-theme-streamlit .ag-root-wrapper": {"border": "0px solid pink !important"},
        ".ag-theme-streamlit .ag-header": {"border": "0px solid pink !important"},
        ".ag-header-cell": {
            "background-color": "#555555", "color": "white",
            "border-bottom": f"2px solid {accent_color} !important"}
    }
    selection = AgGrid(
        df,
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        theme="streamlit",
        height=height,
        custom_css=custom_css,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
    )

    return selection

def fill_out_tossup_values(df):
    tossup_values = ['P', 'G', 'N']
    for entry in tossup_values:
        if entry not in list(df):
            df[entry] = 0
    return df

# @st.experimental_memo

def get_packets():
    packets = {}
    for file in glob.glob('packets/packet*.json'):
        with open(file, 'r') as f:
            packets[file] = json.load(f)
    return packets

def get_packet_meta():
    packets = get_packets()
    packet_meta = []
    for packet in packets.keys():
        for tossup in packets[packet]['tossups']:
            packet_meta.append(
                {
                    'packet': tossup['packetNumber'],
                    'tossup': tossup['questionNumber'],
                    'tossup_length': len(tossup['question'].split(' '))
                }
            )
    return pd.DataFrame(packet_meta)

def calculate_bpa(buzzes, tuh):
    buzzes['bpa_comp'] = buzzes['celerity']*100/tuh
    return(sum(buzzes['bpa_comp']))

def calculate_player_bpas(buzzes, player_stats):
    tossup_meta = load_tossup_meta()
    packet_meta = get_packet_meta()

    buzzes['packet'] = buzzes['packet'].astype(int)

    full_buzzes = buzzes.merge(
        tossup_meta, on=['packet', 'tossup']
    ).merge(
            packet_meta, on=['packet', 'tossup']
        )
    
    full_buzzes['celerity'] = 1 - full_buzzes['buzz_position']/full_buzzes['tossup_length']
    
    player_games = player_stats.groupby(
        ['player', 'team']
        ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})
    player_games['TUH'] = player_games['Games']*20

    player_bpa_list = []
    for i, row in player_games.iterrows():
        player_buzzes = full_buzzes[full_buzzes['value'].isin(['15', '10'])]
        player_buzzes = player_buzzes[player_buzzes['player'] == row['player']]
        player_buzzes = player_buzzes[player_buzzes['team'] == row['team']]
        
        player_bpa_list.append({
            'player': row['player'],
            'team': row['team'],
            'BPA': calculate_bpa(player_buzzes, row['TUH']),
            'ACC': np.mean(player_buzzes['celerity'])
        })
    player_bpa = pd.DataFrame(player_bpa_list)

    packet_tuhs = {
    'History': 4,
    'Science': 4,
    'Literature': 4,
    'Arts': 3,
    'Beliefs': 2,
    'Thought': 2,
    'Other': 1,
    }

    player_cat_bpa_list = []
    for i, row in player_games.iterrows():
        for category, tuh in packet_tuhs.items():
            player_cat_buzzes = full_buzzes[full_buzzes['value'].isin(['15', '10'])]
            player_cat_buzzes = player_cat_buzzes[player_cat_buzzes['player'] == row['player']]
            player_cat_buzzes = player_cat_buzzes[player_cat_buzzes['team'] == row['team']]
            player_cat_buzzes = player_cat_buzzes[player_cat_buzzes['category'] == category]
            player_cat_bpa_list.append({
                    'player': row['player'],
                    'team': row['team'],
                    'category': category,
                    'BPA': calculate_bpa(player_cat_buzzes, row['Games']*tuh),
                    'ACC': np.mean(player_cat_buzzes['celerity'])
                })
    player_cat_bpa = pd.DataFrame(player_cat_bpa_list)

    return player_bpa, player_cat_bpa

def calculate_team_bpas(buzzes, team_stats):
    tossup_meta = load_tossup_meta()
    packet_meta = get_packet_meta()

    buzzes['packet'] = buzzes['packet'].astype(int)

    full_buzzes = buzzes.merge(
    tossup_meta, on=['packet', 'tossup']
    ).merge(
        packet_meta, on=['packet', 'tossup']
        )
    full_buzzes['celerity'] = 1 - full_buzzes['buzz_position']/full_buzzes['tossup_length']
    
    team_games = team_stats.groupby(
        ['team']
        ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})
    team_games['TUH'] = team_games['Games']*20

    team_bpa_list = []
    for i, row in team_games.iterrows():
        team_buzzes = full_buzzes[full_buzzes['value'].isin(['15', '10'])]
        team_buzzes = team_buzzes[team_buzzes['team'] == row['team']]
        team_bpa_list.append({
            'team': row['team'],
            'BPA': calculate_bpa(team_buzzes, row['TUH']),
            'ACC': np.mean(team_buzzes['celerity'])
        })
    team_bpa = pd.DataFrame(team_bpa_list)

    packet_tuhs = {
    'History': 4,
    'Science': 4,
    'Literature': 4,
    'Arts': 3,
    'Beliefs': 2,
    'Thought': 2,
    'Other': 1,
    }

    team_cat_bpa_list = []
    for i, row in team_games.iterrows():
        for category, tuh in packet_tuhs.items():
            team_cat_buzzes = full_buzzes[full_buzzes['value'].isin(['15', '10'])]
            team_cat_buzzes = team_cat_buzzes[team_cat_buzzes['team'] == row['team']]
            team_cat_buzzes = team_cat_buzzes[team_cat_buzzes['category'] == category]
            team_cat_bpa_list.append({
                    'team': row['team'],
                    'category': category,
                    'BPA': calculate_bpa(team_cat_buzzes, row['Games']*tuh),
                    'ACC': np.mean(team_cat_buzzes['celerity'])
                })
    team_cat_bpa = pd.DataFrame(team_cat_bpa_list)

    return team_bpa, team_cat_bpa

def make_scoresheet(game_id, buzzes, bonuses, player_stats):
    game_buzzes = buzzes[buzzes['game_id'] == game_id]
    game_bonuses = bonuses[bonuses['game_id'] == game_id]

    game_buzzes['value'] = game_buzzes['value'].astype(int)
    game_buzzes['answer'] = [sanitize_answer(answer) for answer in game_buzzes['answer']]
    print(game_bonuses['answers'])
    game_bonuses['answers'] = [[sanitize_answer(part) for part in answer.split(' / ')] for answer in game_bonuses['answers']]
    game_bonuses['answers'] = [' / '.join(answers) for answers in game_bonuses['answers']]

    # scoresheet = game_buzzes.pivot(
    #     index = ['tossup'], columns=['team','player'], values='value'
    # ).reset_index().fillna(0).astype(int).astype(str).replace('0', '').reset_index()

    # scoresheet.columns = scoresheet.columns.str.replace(' ', '\n')

    # team_tossups = []
    # for team in player_stats['team']:
    #     player_tossups = []
    #     for player in player_stats[player_stats['team'] == team]['player']:
    #         player_game = [None]*21
    #         for i, row in buzzes[buzzes['team'] == team][buzzes['player'] == player].iterrows():
    #             player_game[row['tossup']] = row['value']
    #         player_tossups.append({'player': player, 'tossups': player_game})
    # print(team_tossups)
    team1_name = game_buzzes['team'].unique().tolist()[0]
    team2_name = game_buzzes['team'].unique().tolist()[1]

    team1_buzzes = game_buzzes[game_buzzes['team'] == team1_name]
    team2_buzzes = game_buzzes[game_buzzes['team'] == team2_name]

    team1_bonuses = game_bonuses[game_bonuses['team'] == team1_name]
    team2_bonuses = game_bonuses[game_bonuses['team'] == team2_name]

    team1_bonuses = team1_bonuses.melt(
        id_vars=['tossup', 'answers'],
        value_vars=['part1_value', 'part2_value', 'part3_value'],
        var_name='part', value_name='value'
    )

    team2_bonuses = team2_bonuses.melt(
        id_vars=['tossup', 'answers'],
        value_vars=['part1_value', 'part2_value', 'part3_value'],
        var_name='part', value_name='value'
    )

    team1_score = []
    team2_score = []
    rscore1 = 0
    rscore2 = 0
    for i in range(1, 21):
        if len(team1_buzzes[team1_buzzes['tossup'] == i]['value']) > 0:
            team1_tossup = sum(
                team1_buzzes[team1_buzzes['tossup'] == i]['value'].tolist())
            team1_bonus = sum(
                team1_bonuses[team1_bonuses['tossup'] == i]['value'].tolist())
            team1_score.append(rscore1 + team1_tossup + team1_bonus)
            rscore1 = rscore1 + team1_tossup + team1_bonus
        else:
            team1_score.append(rscore1)

        if len(team2_buzzes[team2_buzzes['tossup'] == i]['value']) > 0:
            team2_tossup = sum(
                team2_buzzes[team2_buzzes['tossup'] == i]['value'].tolist())
            team2_bonus = sum(
                team2_bonuses[team2_bonuses['tossup'] == i]['value'].tolist())
            team2_score.append(rscore2 + team2_tossup + team2_bonus)
            rscore2 = rscore2 + team2_tossup + team2_bonus
        else:
            team2_score.append(rscore2)

    team1_score_df = pd.DataFrame(
        {'tossup': list(range(1, 21)), 'score': team1_score, 'total': [1]*20})
    team2_score_df = pd.DataFrame(
        {'tossup': list(range(1, 21)), 'score': team2_score, 'total': [1]*20})

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
        x=alt.X(
            "player:N",
            axis=alt.Axis(orient='top', ticks=False, offset=5),
            scale=alt.Scale(
                domain=player_stats[player_stats['team'] == team1_name]['player'].unique()),
            title=None),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=alt.Axis(
                orient='left', domain=False, ticks=False, tickCount=20, title=None, labelAlign='right', labelFontWeight='bold', labelAngle=0
            )),
        text='value:Q',
        tooltip=[alt.Tooltip('answer:N', title="Tossup answer"), alt.Tooltip('buzz_position:Q', title="Buzz location")])
    t1_bonuses = alt.Chart(team1_bonuses).mark_text().encode(
        x=alt.X(
            'part:N',
            axis=alt.Axis(orient='top', ticks=False, labels=False,
                          offset=5, title=wrap(team1_name, width=12))
        ),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=None),
        text='value:Q',
        tooltip=[alt.Tooltip('answers:N', title="Bonus answers")])
    t1_score = alt.Chart(team1_score_df).mark_text().encode(
        x=alt.X('total:N', axis=alt.Axis(orient='top',
                ticks=False, labels=False, offset=5)),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=None),
        text='score:Q')
    t2_tossups = alt.Chart(team2_buzzes).mark_text().encode(
        x=alt.X(
            "player:N",
            axis=alt.Axis(orient='top', ticks=False, offset=5),
            scale=alt.Scale(
                domain=player_stats[player_stats['team'] == team2_name]['player'].unique()),
            title=None),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=alt.Axis(
                orient='left', grid=False, ticks=False, tickCount=20, title=None, labelAlign='right', labelFontWeight='bold', labelAngle=0
            )),
        text='value:Q',
        tooltip=[alt.Tooltip('answer:N', title="Tossup answer"), alt.Tooltip('buzz_position:Q', title="Buzz location")])
    t2_bonuses = alt.Chart(team2_bonuses).mark_text().encode(
        x=alt.X(
            'part:N',
            axis=alt.Axis(orient='top', ticks=False, labels=False,
                          offset=5, title=wrap(team2_name, width=12))
        ),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=None),
        text='value:Q',
        tooltip=[alt.Tooltip('answers:N', title="Bonus answers")])
    t2_score = alt.Chart(team2_score_df).mark_text().encode(
        x=alt.X('total:N', axis=alt.Axis(orient='top',
                ticks=False, offset=5, labels=False)),
        y=alt.Y(
            'tossup:O',
            scale=alt.Scale(domain=list(range(1, 21))),
            axis=None),
        text='score:Q')

    player_grid = alt.Chart(all_player_cells).mark_rect(
        stroke='black', strokeWidth=.1, fill=None
    ).encode(
        x='player:N', y=alt.Y('tossup:O'), detail='count()'
    )

    bonus_grid = alt.Chart(all_bonus_cells).mark_rect(
        stroke='black', strokeWidth=.1, fill=None
    ).encode(
        x='part:N', y='tossup:O'
    )

    total_grid = alt.Chart(all_total_cells).mark_rect(
        stroke='black', strokeWidth=.1, fill=None
    ).encode(
        x='total:N', y='tossup:O'
    )

    return alt.hconcat(
        alt.hconcat(t1_tossups + player_grid, t1_bonuses +
                    bonus_grid, t1_score + total_grid, spacing=10),
        alt.hconcat(t2_tossups + player_grid, t2_bonuses +
                    bonus_grid, t2_score + total_grid, spacing=10),
        spacing=-10).configure(
            font='Segoe UI'
    ).configure_view(strokeWidth=0).configure_axis(grid=False, labelAngle=45).configure_text(size=11)
    # return team1_buzzes

def df_to_kable(df):
    df.to_csv('temp_df.csv', index = False)
    process = subprocess.Popen("Rscript kable.R", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell = True)
    result = process.communicate()
    st.markdown(result[0], unsafe_allow_html=True)

def df_to_dt(df):
    df.to_csv('temp_df.csv', index = False)
    process = subprocess.Popen("Rscript dt.R", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell = True)
    result = process.communicate()
    st.markdown(result[0], unsafe_allow_html=True)