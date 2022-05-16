import streamlit as st
from st_click_detector import click_detector
import utils


def app(tournaments, divisions, accent_color):
    st.title(f'QB League Season {tournaments} -- Games')
    st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
                unsafe_allow_html=True)
    
    buzzes = utils.load_buzzes(tournaments)
    bonuses = utils.load_bonuses(tournaments)
    tossup_meta = utils.load_tossup_meta()
    bonus_meta = utils.load_bonus_meta()
    team_stats = utils.load_team_stats(tournaments)
    player_stats = utils.load_player_stats(tournaments)

    full_buzzes = buzzes.merge(tossup_meta[tossup_meta['season'] == tournaments], on=['packet', 'tossup'])
    full_buzzes['division'] = [x.split('-')[1] for x in full_buzzes['game_id']]

    full_bonuses = bonuses.merge(bonus_meta[bonus_meta['season'] == tournaments], on=['packet', 'bonus'])
    full_bonuses['division'] = [x.split('-')[1] for x in full_bonuses['game_id']]

    if len(divisions) > 0:
        full_buzzes = full_buzzes[full_buzzes['division'].isin(divisions)]
        full_bonuses = full_bonuses[full_bonuses['division'].isin(divisions)]

    if tournaments == 1:
        st.write("Game scoresheets not available for season 1 due to technical error -- may be reconstructed in the future.")

    else:
        games, scoresheets = st.columns(2)

        @st.cache
        def generate_links():
            links = []
            toc = ['<ul id="table-of-contents">']

            for pac in team_stats['packet'].unique():
                toc.append(f"<li><a href='#packet-{int(pac)}'>Packet {int(pac)}</a></li>")
            toc.append('</ul>')
            links.append(' '.join(toc))
            for pac in team_stats['packet'].unique():
                links.append(f"<h2 id = 'packet-{int(pac)}'>Packet {int(pac)}</h2>")
                for i in team_stats[team_stats['packet'] == pac]['game_id'].unique():
                    # print(team_stats[team_stats['game_id'] == i]['total_points'])
                    team1_score = team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0]
                    team2_score = team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1]
                    if team1_score > team2_score:
                        line = f"""{team_stats[team_stats['game_id'] == i]['team'].tolist()[0]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0])},
                        {team_stats[team_stats['game_id'] == i]['team'].tolist()[1]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1])}"""
                    else:
                        line = f"""{team_stats[team_stats['game_id'] == i]['team'].tolist()[1]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1])},
                        {team_stats[team_stats['game_id'] == i]['team'].tolist()[0]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0])}"""
                    links.append(f"<p><a href='#top' id='{i}'>{line}</a></p>")
            content = ' '.join(links)
            return content

        with games:
            clicked = click_detector(generate_links())

        # scoresheets.markdown(f"**{clicked} clicked**" if clicked != "" else "**No click**")
        # scoresheets.dataframe(utils.make_scoresheet(clicked, full_buzzes, full_bonuses, player_stats))
        game_player_stats = player_stats[player_stats['game_id'] == clicked]
        c = utils.make_scoresheet(clicked, full_buzzes, full_bonuses, game_player_stats)

        scoresheets.altair_chart(c)
        # scoresheets.dataframe(c)