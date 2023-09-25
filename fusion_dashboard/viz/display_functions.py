import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_BST_delta_scatter(input_data: pd.DataFrame):
    # Calculate a combined color value based on 'Effective Delta' and 'BST'
    # You can customize the calculation as needed
    input_data['Composite Strength'] = ((input_data['Effective Delta'] * 15) + input_data['Bst']) / 2

    # Create a scatter plot with hover text using plotly
    fig = px.scatter(
        input_data,
        x='Effective Delta',
        y='Bst',
        color='Composite Strength',
        color_continuous_scale='RdYlGn',  # Green to red color scale
        title='Effective Delta vs. BST',
        hover_data=['Head', 'Body'],  # Specify columns to display in tooltips
    )

    # Customize the plot
    fig.update_xaxes(title='Effective Delta')
    fig.update_yaxes(title='BST')

    return fig


def build_BST_stacked_bar(input_data: pd.DataFrame):

    # Define the stats columns in the desired order
    stats_columns = ['Hp', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']

    # Create a list to store the data for each stat
    data = []

    # Iterate through the stats columns to create inverted stacked bars
    for stat in stats_columns[::-1]:
        bar = go.Bar(
            x=input_data.index,
            y=input_data[stat],
            name=stat,
            hovertemplate='%{y}',  # Display the stat name and value on hover
            marker=dict(line=dict(width=0)),  # Remove bar outline
        )
        data.append(bar)

    # Define the layout for the stacked bar chart
    layout = go.Layout(
        barmode='stack',
        title='Pokémon Stats',
        xaxis=dict(
            tickvals=input_data.index,
            ticktext=input_data['Head'] + ' & ' + input_data['Body'],
            tickangle=-45,
        ),
        xaxis_title='Pokémon Pair',
        yaxis_title='BST',
        legend_title='Stats',
        showlegend=True,
    )

    # Create the Plotly figure
    fig = go.Figure(data=data, layout=layout)

    return fig


def build_cumulative_stat_bar(input_data: pd.DataFrame):
    # Calculate the cumulative values for each stat
    stats = ['Hp', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']
    cumulative_stats = input_data[stats].sum()

    # Sort the cumulative stats in descending order
    cumulative_stats = cumulative_stats.sort_values(ascending=True)

    # Create a horizontal bar graph
    fig = px.bar(
        x=cumulative_stats.values,
        y=cumulative_stats.index,
        orientation='h',
        labels={'x': 'Cumulative BST', 'y': 'Stat'},
        title='Cumulative Stats for Team',
        color=cumulative_stats.values,  # Assign color based on values
        color_continuous_scale='RdYlGn',  # Use the defined color scale
    )

    return fig


def build_weaknesses_scatter(input_data: pd.DataFrame):
    # Define a list of types to consider
    types_to_consider = ['Electric', 'Psychic', 'Fire', 'Water', 'Ice', 'Fighting', 'Grass', 'Ground', 'Dark', 'Ghost', 'Bug', 'Poison', 'Steel', 'Flying', 'Normal', 'Fairy', 'Dragon']

    # Initialize lists to store data for the scatter plot
    weakness_counts = []
    resist_or_immunity_counts = []

    # Remove None values here
    input_data['Super Weaknesses'] = input_data['Super Weaknesses'].fillna('')
    input_data['Super Resistances'] = input_data['Super Resistances'].fillna('')
    input_data['Immunities'] = input_data['Immunities'].fillna('')

    # Calculate the number of pairs weak to each type and the number of pairs that resist or are immune to each type
    for pokemon_type in types_to_consider:
        # Count pairs weak to the type
        weak_to_type = input_data[input_data['Normal Weaknesses'].str.contains(pokemon_type, case=False, na=False) | input_data['Super Weaknesses'].str.contains(pokemon_type, case=False, na=False)]
        weakness_counts.append(len(weak_to_type))

        # Count pairs that resist or are immune to the type
        resist_or_immunity_to_type = input_data[input_data['Normal Resistances'].str.contains(pokemon_type, case=False, na=False) | input_data['Super Resistances'].str.contains(pokemon_type, case=False, na=False) | input_data['Immunities'].str.contains(pokemon_type, case=False, na=False)]
        resist_or_immunity_counts.append(len(resist_or_immunity_to_type))

    # Create a DataFrame for the scatter plot
    scatter_df = pd.DataFrame({'Type': types_to_consider, 'Weakness Count': weakness_counts, 'Resist Count': resist_or_immunity_counts})

    # Calculate the Danger score
    scatter_df['Danger'] = scatter_df['Weakness Count'] - scatter_df['Resist Count']

    # Group the records and combine the 'Type' values
    grouped_records = scatter_df.groupby(['Weakness Count', 'Resist Count'])['Type'].apply('/'.join).reset_index()

    # Create a 'Danger' column based on the Danger score for coloring
    grouped_records['Danger'] = grouped_records['Weakness Count'] - grouped_records['Resist Count']

    # Create a scatter plot with color ramp
    fig = px.scatter(
        grouped_records, x='Weakness Count', y='Resist Count', text='Type',
        color='Danger', color_continuous_scale='RdYlGn_r',
        title='Team Weaknesses vs. Resistances',
    )

    # Customize the x-axis ticks to be integers
    fig.update_xaxes(tick0=0, dtick=1)

    # Customize the plot
    fig.update_traces(textposition='top center', marker=dict(size=14))

    return fig


def build_individual_weak_chart(input_data: pd.DataFrame):
    types = ['Normal Resistances', 'Super Resistances', 'Normal Weaknesses', 'Super Weaknesses', 'Immunities']

    # Initialize an empty list to store data
    data = []

    # Iterate through each row and type to create data points
    for index, row in input_data.iterrows():
        for type_name in types:
            type_values = row[type_name]
            if pd.notna(type_values) and type_values.strip() != '':
                type_values = type_values.split(', ')

                for val in type_values:
                    if type_name == 'Normal Resistances':
                        multiplier = 0.5
                    elif type_name == 'Super Resistances':
                        multiplier = 0.25
                    elif type_name == 'Immunities':
                        multiplier = 0
                    elif type_name == 'Normal Weaknesses':
                        multiplier = 2
                    elif type_name == 'Super Weaknesses':
                        multiplier = 4

                    data.append({'Pokemon': f"{row['Head']} / {row['Body']}", 'Type': val, 'Category': multiplier})

    # Create a DataFrame from the data list
    heatmap_df = pd.DataFrame(data)

    pivot = heatmap_df.pivot(index='Pokemon', columns='Type', values='Category').fillna(1)

    # Create a heatmap
    fig = px.imshow(pivot, color_continuous_scale='RdYlGn_r', color_continuous_midpoint=1, text_auto=True)
    fig.update_layout(
        title='Pokémon Weaknesses and Resistances',
        xaxis_title='Type',
        yaxis_title='Pokémon',
        xaxis_nticks=len(heatmap_df['Type'].unique()),  # Display all Pokemon
        yaxis_nticks=len(heatmap_df['Pokemon'].unique()),      # Display all Types
        xaxis_showticklabels=True,  # Show Pokemon names
        yaxis_showticklabels=True,   # Show Type names
    )

    return fig


def build_offensive_threat_scatter(input_data):
    types = list(input_data.keys())
    scores = list(input_data.values())

    # Create a DataFrame from the results
    df = pd.DataFrame({'Types': types, 'Scores': scores})

    # Create a scatter plot using Plotly Express
    fig = px.scatter(
        df, x='Types', y='Scores', color='Scores',
        color_continuous_scale='RdYlGn_r',
        labels={'Scores': 'Threat Score'},
        title='Composite Offensive Threat Scores for All Types',
    )

    # Customize the plot
    fig.update_traces(marker_size=30, selector=dict(mode='markers+text'))

    # Add a color bar
    fig.update_layout(coloraxis_colorbar=dict(title='Threat Score'))

    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45, tickvals=list(range(len(types))), ticktext=types)

    return fig
