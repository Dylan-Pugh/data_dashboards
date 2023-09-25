import json
import streamlit as st
import pandas as pd
from viz import display_functions
from processing import offensive_threat_calculator


st.set_page_config(layout='wide', page_icon=':chart_with_upwards_trend:')


# Function to calculate and display scores
def calculate_and_display_scores(weights, offensive_potentials):
    sorted_potentials = offensive_threat_calculator.calculate_composite_offensive_threat_score(offensive_potentials, weights)

    # Sort by score
    sorted_potentials = dict(sorted(sorted_potentials.items(), key=lambda item: item[1], reverse=True))

    # Round
    sorted_potentials = {key: round(value, 2) for key, value in sorted_potentials.items()}

    # Display the scores
    threat_score_scatter = display_functions.build_offensive_threat_scatter(sorted_potentials)
    st.plotly_chart(threat_score_scatter, use_container_width=True)

    # Create a DataFrame from the dictionary
    data_df = pd.DataFrame({'Type': sorted_potentials.keys(), 'Offensive Score': sorted_potentials.values()})

    # Capitalize the 'Type' column
    data_df['Type'] = data_df['Type'].str.capitalize()

    # Display the DataFrame as a table
    with st.expander(label='Table of Scores'):
        st.dataframe(data_df, use_container_width=True, hide_index=True)

    with open('fusion_dashboard/data/threat_scores.json', 'w') as json_file:
        json.dump(sorted_potentials, json_file)


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


# Open the JSON file for reading
file = open('fusion_dashboard/data/offensive_potentials_V3.json')
offensive_potentials = json.load(file)

# Close the file when you're done with it
file.close()

# Define the weights object
weights = {
    'Super_Effective_Count': 2,
    'Resisted_Count': 1,
    'Move_Count': 0.1,
    'Average_Power': 1.5,
    'Pokemon_with_Moves_Count': 1.5,
    'Pokemon_with_STAB': 1,
    'Average_Attack': 0.5,
    'Average_Special_Attack': 0.5,
    'STAB_Average_Attack': 1,
    'STAB_Average_Special_Attack': 1,
}

# Create sliders for each metric and allow the user to set the weights
st.title('Weight Configuration')

# Create two columns for sliders
col1, col2 = st.columns(2)

# Display sliders in the first column
with col1:
    for metric, default_weight in list(weights.items())[:5]:
        weight = st.slider(
            f"{metric.replace('_', ' ').title()}",
            min_value=0.0,
            max_value=3.0,
            step=0.1,
            value=float(default_weight),
        )
        weights[metric] = weight

# Display sliders in the second column
with col2:
    for metric, default_weight in list(weights.items())[5:]:
        weight = st.slider(
            f"{metric.replace('_', ' ').title()}",
            min_value=0.0,
            max_value=3.0,
            step=0.1,
            value=float(default_weight),
        )
        weights[metric] = weight

# Call the function to calculate and display scores
calculate_and_display_scores(weights, offensive_potentials)
