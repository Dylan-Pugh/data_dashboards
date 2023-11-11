import streamlit as st
import pandas as pd
from viz import display_functions, pokemon_tile
from processing import fusion_functions

st.set_page_config(layout='wide', page_icon=':bar_chart:')


@st.cache_data
def display_fusion_results(df):
    st.header('Analysis', divider='rainbow')
    # Display table of fusions
    st.dataframe(
        df, use_container_width=True, hide_index=True, column_order=[
            'Head',
            'Body',
            'Primary Type',
            'Secondary Type',
            'Hp',
            'Attack',
            'Defense',
            'Special Attack',
            'Special Defense',
            'Speed',
            'Bst',
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
    scatter = display_functions.build_BST_delta_scatter(df)
    st.plotly_chart(scatter, use_container_width=True)

    # Show stacked bar plot
    stacked_bar = display_functions.build_BST_stacked_bar(df)
    st.plotly_chart(stacked_bar, use_container_width=True)

    # Show cumulative stats bar
    cumulative_bar = display_functions.build_cumulative_stat_bar(df)
    st.plotly_chart(cumulative_bar, use_container_width=True)

    # Show weaknesses scatter
    weak_scatter = display_functions.build_weaknesses_scatter(df)
    st.plotly_chart(weak_scatter, use_container_width=True)

    # Show weaknesses chart
    weak_chart = display_functions.build_individual_weak_chart(df)
    st.plotly_chart(weak_chart, use_container_width=True)


@st.cache_data
def display_team_status():
    st.header('Team Status', divider='rainbow')

    col1, col2, col3 = st.columns([2, 2, 2])

    for index, row in st.session_state['current_team'].iterrows():
        if index < 2:
            col = col1
        elif index < 4:
            col = col2
        else:
            col = col3

        with col:
            pokemon_tile.st_pokemon_tile(row)

    if st.button(label='Calculate Type Coverage'):
        coverage_data = []
        combined_moveset = []
        for current in st.session_state.keys():
            if current.endswith('move_select'):
                mon_coverage = fusion_functions.get_type_coverage(st.session_state[current])
                combined_moveset += st.session_state[current]

                # Parse current mon
                head, body = current.split('/')[0], current.split('/')[1].split('_')[0]

                # Parse out moveset coverage
                for damage_relation in mon_coverage.keys():
                    if damage_relation == 'double_damage_to':
                        multiplier = 2
                    elif damage_relation == 'neutral_damage_to':
                        multiplier = 1
                    elif damage_relation == 'half_damage_to':
                        multiplier = 0.5
                    elif damage_relation == 'no_damage_to':
                        multiplier = 0

                    for type in mon_coverage[damage_relation]:
                        coverage_data.append({
                            'Pokemon': f'{head} / {body}',
                            'Type': type.capitalize(),
                            'Category': multiplier,
                        })

        # Parse out moveset coverage
        team_coverage = fusion_functions.get_type_coverage(combined_moveset)

        for damage_relation in team_coverage.keys():
            if damage_relation == 'double_damage_to':
                multiplier = 2
            elif damage_relation == 'neutral_damage_to':
                multiplier = 1
            elif damage_relation == 'half_damage_to':
                multiplier = 0.5
            elif damage_relation == 'no_damage_to':
                multiplier = 0

            for type in team_coverage[damage_relation]:
                coverage_data.append({
                    'Pokemon': 'Team',
                    'Type': type.capitalize(),
                    'Category': multiplier,
                })

        offfensive_coverage_chart = display_functions.build_individual_weak_chart(
            input_data=coverage_data,
            extract_data=False,
            invert_scale=False,
        )

        st.plotly_chart(offfensive_coverage_chart, use_container_width=True)


df = pd.read_csv('fusion_dashboard/data/current_dex.csv')

if 'current_team' not in st.session_state:
    st.session_state['current_team'] = None

default_bodies = None
default_heads = None

if st.session_state['current_team'] is not None:
    # Initialize with current data, if it exists
    current_team = st.session_state['current_team']

    default_heads = current_team['Head'].tolist()
    default_heads = [head.capitalize() for head in default_heads]

    default_bodies = current_team['Body'].tolist()
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

if st.button('Analyze Team'):
    fused_team = fusion_functions.create_fused_team(fusion_pairs, adjust_for_threat_score)
    st.session_state['current_team'] = fused_team
    display_fusion_results(fused_team)
    display_team_status()
elif st.session_state['current_team'] is not None:
    display_fusion_results(st.session_state['current_team'])
    display_team_status()
