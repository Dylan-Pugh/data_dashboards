import os
import streamlit as st
import pandas as pd
from viz import display_functions
from processing import fusion_functions

st.set_page_config(layout='wide', page_icon=':bar_chart:')


def display_fusion_results(df):
    # Display table of fusions
    st.dataframe(df, use_container_width=True, hide_index=True)

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


df = pd.read_csv('fusion_dashboard/data/current_dex.csv')

load_team = False

if os.path.exists('fusion_dashboard/data/current_team.csv'):
    # Initialize with current data, if it exists
    current_team = pd.read_csv('fusion_dashboard/data/current_team.csv')
    load_team = True

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
    fusion_functions.create_fused_team(fusion_pairs, adjust_for_threat_score)

    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv('fusion_dashboard/data/current_team.csv')

    display_fusion_results(df)
elif load_team:
    display_fusion_results(current_team)
