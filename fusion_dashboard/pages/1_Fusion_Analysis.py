import pandas as pd
import streamlit as st

from processing import fusion_functions
from viz import display_functions


st.set_page_config(layout='wide', page_icon=':dna:')


@st.cache_data
def display_fusion_results(df):
    """Display fusion results dataframe."""
    st.header('Analysis', divider='rainbow')
    # Display table of fusions
    st.dataframe(
        df, use_container_width=True, hide_index=True, column_order=[
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
    scatter = display_functions.build_BST_delta_scatter(df)
    st.plotly_chart(scatter, use_container_width=True)

    # Show stacked bar plot
    stacked_bar = display_functions.build_BST_stacked_bar(df)
    st.plotly_chart(stacked_bar, use_container_width=True)


if 'current_fusions' not in st.session_state:
    st.session_state['current_fusions'] = None

default_fusions = None
if st.session_state['current_fusions'] is not None:
    default_fusions = set(st.session_state['current_fusions']['Head'].tolist())
    default_fusions = [mon.capitalize() for mon in default_fusions]

df = pd.read_csv('fusion_dashboard/data/current_dex.csv')
options = df['NAME'].to_list()

selection = st.multiselect(
    label='Select Input Pokémon',
    options=[opt.capitalize() for opt in options],
    default=default_fusions if default_fusions else None,
)

# Save selection to new list
user_selection = []
for item in selection:
    user_selection.append(item)

# Only include useful columns
metric = st.selectbox(
    label='Metric to Prioritize (only for optimal fusions)',
    options=[
        'HP',
        'Attack',
        'Defense',
        'Special Attack',
        'Special Defense',
        'Speed',
        'BST',
        'Effective Delta',
        'Total Weaknesses',
    ],
)

adjust_for_threat_score = st.toggle(label='Adjust for threat scores', value=False)

if st.button('Find All Fusions'):
    possible_fusions = fusion_functions.get_possible_fusions(user_selection, adjust_for_threat_score)
    st.session_state['current_fusions'] = possible_fusions
    display_fusion_results(possible_fusions)
elif st.button('Find Optimal Fusions'):
    all_fusions = fusion_functions.get_possible_fusions(user_selection, adjust_for_threat_score)
    st.session_state['current_fusions'] = all_fusions

    optimal_fusions = fusion_functions.get_optimal_fusions(all_fusions, prioritized_metric=metric)
    display_fusion_results(optimal_fusions)
elif st.session_state['current_fusions'] is not None:
    display_fusion_results(st.session_state['current_fusions'])
