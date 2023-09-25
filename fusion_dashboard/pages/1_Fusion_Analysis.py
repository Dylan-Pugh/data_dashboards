import os
import streamlit as st
import pandas as pd
from viz import display_functions
from processing import fusion_functions


st.set_page_config(layout='wide', page_icon=':dna:')


def display_fusion_results(df):
    # Display table of fusions
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Show scatter plot
    scatter = display_functions.build_BST_delta_scatter(df)
    st.plotly_chart(scatter, use_container_width=True)

    # Show stacked bar plot
    stacked_bar = display_functions.build_BST_stacked_bar(df)
    st.plotly_chart(stacked_bar, use_container_width=True)


df = pd.read_csv('fusion_dashboard/data/current_dex.csv')

load_fusions = False

if os.path.exists('fusion_dashboard/data/possible_fusions.csv'):
    # Initialize with current data, if it exists
    current_selection = pd.read_csv('fusion_dashboard/data/possible_fusions.csv')
    load_fusions = True

    default_fusions = set(current_selection['Head'].tolist())
    default_fusions = [mon.capitalize() for mon in default_fusions]

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
        'Hp',
        'Attack',
        'Defense',
        'Special Attack',
        'Special Defense',
        'Speed',
        'Bst',
        'Effective Delta',
    ],
)

adjust_for_threat_score = st.toggle(label='Adjust for threat scores', value=False)

if st.button('Find All Fusions'):
    fusion_functions.get_possible_fusions(user_selection, adjust_for_threat_score)
    df = pd.read_csv('fusion_dashboard/data/possible_fusions.csv')
    display_fusion_results(df)
elif st.button('Find Optimal Fusions'):
    fusion_functions.get_possible_fusions(user_selection, adjust_for_threat_score)
    all_fusions = pd.read_csv('fusion_dashboard/data/possible_fusions.csv')
    fusion_functions.get_optimal_fusions(all_fusions, prioritized_metric=metric)
    df = pd.read_csv('fusion_dashboard/data/optimal_fusions.csv')
    display_fusion_results(df)
elif load_fusions:
    display_fusion_results(current_selection)
