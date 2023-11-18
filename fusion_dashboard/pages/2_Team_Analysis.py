import streamlit as st
import pandas as pd
from viz import display_functions, pokemon_tile
from processing import fusion_functions

st.set_page_config(layout='wide', page_icon=':bar_chart:')


@st.cache_data
def display_fusion_results(df):
    # Filter out the 'Team' entry
    filtered_df = df[df['ID'] != 0].copy()

    st.header('Analysis', divider='rainbow')
    # Display table of fusions
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_order=[
            'Head',
            'Body',
            'Primary Type',
            'Secondary Type',
            'HP',
            'Attack',
            'Defense',
            'Special Attack',
            'Special Defense',
            'Speed',
            'BST',
            'Effective Delta',
            'Total Resistances',
            'Total Weaknesses',
            'Normal Resistances',
            'Super Resistances',
            'Immunities',
            'Normal Weaknesses',
            'Super Weaknesses',
        ],
    )

    # Show scatter plot
    scatter = display_functions.build_BST_delta_scatter(filtered_df)
    st.plotly_chart(scatter, use_container_width=True)

    # Show stacked bar plot
    stacked_bar = display_functions.build_BST_stacked_bar(filtered_df)
    st.plotly_chart(stacked_bar, use_container_width=True)

    # Show cumulative stats bar
    cumulative_bar = display_functions.build_cumulative_stat_bar(filtered_df)
    st.plotly_chart(cumulative_bar, use_container_width=True)

    # Show weaknesses scatter
    weak_scatter = display_functions.build_weaknesses_scatter(filtered_df)
    st.plotly_chart(weak_scatter, use_container_width=True)

    # Show weaknesses chart
    weak_chart = display_functions.build_type_relationship_chart(df)
    st.plotly_chart(weak_chart, use_container_width=True)


# @st.cache_data
def display_team_status():
    st.header('Team Status', divider='rainbow')

    if (
        st.button(label='Update & Calculate Type Coverage')
        or st.session_state['current_team'] is not None
    ):
        fusion_functions.calc_team_coverage(st.session_state['current_team'])

        offensive_coverage_chart = display_functions.build_type_relationship_chart(
            input_data=st.session_state['current_team'],
            invert=False,
        )

        if offensive_coverage_chart is not None:
            st.plotly_chart(offensive_coverage_chart, use_container_width=True)

    col1, col2, col3 = st.columns([2, 2, 2])

    for index, row in st.session_state['current_team'].iterrows():

        if row['ID'] == 0:
            continue

        if index == 1 or index == 4:
            col = col1
        elif index == 2 or index == 5:
            col = col2
        else:
            col = col3

        with col:
            pokemon_tile.st_pokemon_tile(row)


df = pd.read_csv('fusion_dashboard/data/current_dex.csv')

if 'current_team' not in st.session_state:
    st.session_state['current_team'] = None

default_bodies = None
default_heads = None

if st.session_state['current_team'] is not None:
    # Initialize with current data, if it exists
    current_team = st.session_state['current_team']

    default_heads = [value for value in current_team['Head'].tolist() if isinstance(value, str)]
    default_heads = [head.capitalize() for head in default_heads]

    default_bodies = [value for value in current_team['Body'].tolist() if isinstance(value, str)]
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

adjust_for_threat_score = st.toggle(label='Adjust for threat scores', value=False)

if st.session_state['current_team'] is not None:
    st.download_button(
        label='Download Team',
        data=fusion_functions.get_team_csv(st.session_state['current_team']),
        file_name='current_team.csv',
        mime='text/csv',
    )

if st.button('Analyze Team'):
    fused_team = fusion_functions.create_fused_team(
        fusion_pairs, adjust_for_threat_score,
    )
    st.session_state['current_team'] = fused_team
    display_fusion_results(fused_team)
    display_team_status()
elif st.session_state['current_team'] is not None:
    display_fusion_results(st.session_state['current_team'])
    display_team_status()
