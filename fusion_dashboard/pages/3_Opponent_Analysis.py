import streamlit as st
import pandas as pd
from viz import display_functions
from processing import fusion_functions

st.set_page_config(layout='wide', page_icon=':bar_chart:')


def highlight_survived(s):
    return ['background-color: #f26d6d']*len(s) if s.Caution else ['background-color: #37bbf0']*len(s)


@st.cache_data
def display_opponent_analysis(df, opponent_level):
    st.header('Analysis', divider='rainbow')
    # Extract Head, Body, Primary, and Secondary Types
    head = df['Head'].iloc[0]
    body = df['Body'].iloc[0]
    primary_type = df['Primary Type'].iloc[0]
    secondary_type = df['Secondary Type'].iloc[0]

    if secondary_type and secondary_type != 'None':
        type_string = f'{primary_type.capitalize()}/{secondary_type.capitalize()}'
    else:
        type_string = primary_type.capitalize()

    # Display the information using st.markdown
    st.header(f'You Are Facing: {head.capitalize()}/{body.capitalize()}')
    st.header(f'Type: {type_string}')

    # Show stat bars
    stats_bar = display_functions.build_individual_stat_bars(df)
    st.plotly_chart(stats_bar, use_container_width=True)

    # Show weaknesses chart
    weak_chart = display_functions.build_individual_weak_chart(df)
    st.plotly_chart(weak_chart, use_container_width=True)

    # Handle learnsets
    learnset = df['Learnset'].to_dict()

    filtered_dict = {key: value for key, value in learnset[0].items() if key <= opponent_level}

    # Extract all values into a list
    all_moves = [move for moves in filtered_dict.values() for move in moves]

    moves_df = fusion_functions.analyze_moveset(all_moves)

    # Display the table with highlighted rows
    st.write('Known Moves:')
    st.dataframe(
        moves_df.style.apply(highlight_survived, axis=1),
        use_container_width=True,
        hide_index=True,
        column_order=['Move', 'Type', 'Power'],
    )


df = pd.read_csv('fusion_dashboard/data/current_dex.csv')

if 'current_opponent' not in st.session_state:
    st.session_state['current_opponent'] = None

default_bodies = None
default_heads = None

if st.session_state['current_opponent'] is not None:
    # Initialize with current data, if it exists
    current_opponent = st.session_state['current_opponent']

    default_heads = current_opponent['Head'].tolist()
    default_heads = [head.capitalize() for head in default_heads]

    default_bodies = current_opponent['Body'].tolist()
    default_bodies = [body.capitalize() for body in default_bodies]

head_options = df['NAME'].to_list()
body_options = df['NAME'].to_list()

# Here make default options current values from spreadsheet
head_selection = st.multiselect(
    label='Select Head Pokémon',
    options=[opt.capitalize() for opt in head_options],
    max_selections=6,
    default=default_heads if default_heads else None,
)
body_selection = st.multiselect(
    label='Select Body Pokémon',
    options=[opt.capitalize() for opt in body_options],
    max_selections=6,
    default=default_bodies if default_bodies else None,
)

# Combine head and body selections into list of tuples
fusion_pairs = list(zip(head_selection, body_selection))

st.write('Selected:')
for pair in fusion_pairs:
    st.write(f'- Head: {pair[0]}, Body: {pair[1]}')

opponent_level = st.number_input(label='Opponent Level', value=20, min_value=1, max_value=100)
adjust_for_threat_score = st.toggle(label='Adjust for threat scores', value=False)

if st.button('Analyze Opponent'):
    fused_team = fusion_functions.create_fused_team(fusion_pairs, adjust_for_threat_score)
    st.session_state['current_opponent'] = fused_team
    display_opponent_analysis(fused_team, opponent_level)
elif st.session_state['current_opponent'] is not None:
    display_opponent_analysis(st.session_state['current_opponent'], opponent_level)
