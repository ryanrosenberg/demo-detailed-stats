import streamlit as st
st.set_page_config(layout="wide")
import utils

for k, v in st.session_state.items():
    st.session_state[k] = v

utils.local_css("style.css")

st.title('2022 NASAT Tossups')

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
category_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['category']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
category_acc['ACC'] = round(category_acc['ACC'], 3)

subcategory_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['category', 'subcategory']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
subcategory_acc['ACC'] = round(subcategory_acc['ACC'], 3)

tossup_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['packet', 'tossup', 'category', 'subcategory']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
tossup_acc['ACC'] = round(tossup_acc['ACC'], 3)

tossup_summary = full_buzzes.groupby(
        ['packet', 'tossup', 'category', 'subcategory', 'answer', 'value']
        ).agg(
            'size'
            ).reset_index().pivot(
                index = ['packet', 'tossup', 'category', 'subcategory', 'answer',], columns='value', values=0
                ).reset_index().rename(columns={10: 'G', -5:'N'})

for x in ['G', 'N']:
        if x not in tossup_summary.columns:
            tossup_summary[x] = 0

packet_games = full_buzzes.groupby('packet').agg(
    {'game_id': 'nunique'}
    ).reset_index().rename(columns={'game_id': 'TU'})
packet_games[['packet']] = packet_games[['packet']].astype(int)

tossup_table = tossup_summary.merge(packet_games, on = 'packet')
tossup_table['answer'] = [utils.sanitize_answer(answer) for answer in tossup_table['answer']]
tossup_table = tossup_table[['packet', 'tossup', 'category', 'subcategory', 'answer', 'TU', 'G', 'N']].fillna(0)
tossup_table[['packet', 'G', 'N']] = tossup_table[['packet', 'G', 'N']].astype(int)
tossup_table = tossup_table.assign(
    conv_pct = lambda x: round((x.G)/x.TU, 3), 
    neg_pct = lambda x: round(x.N/x.TU, 3)
    ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
        tossup_acc, on = ['packet', 'tossup', 'category', 'subcategory']
    )

category_summary = tossup_table.groupby(['category'], as_index=False).agg(
    {'TU': 'sum', 'G': 'sum', 'N': 'sum'}
    ).assign(
    conv_pct = lambda x: round((x.G)/x.TU, 3), 
    neg_pct = lambda x: round(x.N/x.TU, 3)
    ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
        category_acc, on = 'category'
    )
subcategory_summary = tossup_table.groupby(['category', 'subcategory'], as_index=False).agg(
    {'TU': 'sum', 'G': 'sum', 'N': 'sum'}
    ).assign(
    conv_pct = lambda x: round((x.G)/x.TU, 3), 
    neg_pct = lambda x: round(x.N/x.TU, 3)
    ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
        subcategory_acc, on = ['category', 'subcategory']
    )

col1, col2 = st.columns(2)

with col1:
    st.header('Category Summary')
    utils.df_to_kable(category_summary)    
with col2:
    st.header('Subcategory Summary')
    utils.df_to_kable(subcategory_summary) 
utils.hr()
st.header('All Tossups')         
utils.aggrid_interactive_table(tossup_table)