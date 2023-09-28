import json
import pandas as pd
import requests
import streamlit as st
from data import static_types


def get_pokemon_df(input_pokemon):
    # Preprocess the input data
    for entry in input_pokemon:
        stats = entry.get('Stats')
        if stats:
            # Convert stats from a dictionary to separate columns
            entry.update(stats)
            entry.pop('Stats')

        # Remove curly braces from sets and convert to comma-separated strings
        for key, value in entry.items():
            if isinstance(value, set):
                entry[key] = ', '.join(value)

    # Define the desired column order and rename columns
    column_order = [
        'head', 'body', 'primary_type', 'secondary_type',
        'HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed', 'BST',
        'Normal_Resistances', 'Super_Resistances', 'Immunities',
        'Normal_Weaknesses', 'Super_Weaknesses',
        'Total_resistances', 'Total_weaknesses', 'Effective_delta',
    ]

    # Create a Pandas DataFrame from the list of dictionaries with reordered columns and renamed columns
    df = pd.DataFrame(input_pokemon, columns=column_order)

    # Normalize column names (replace underscores with spaces and capitalize each word)
    df.columns = [col.replace('_', ' ').title() for col in df.columns]

    return df


def get_type_data(type_name):
    response = requests.get(f'https://pokeapi.co/api/v2/type/{type_name}')
    type_data = response.json()
    return type_data


def get_pokemon_info(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        species = data['species']['name']
        primary_type = data['types'][0]['type']['name']
        secondary_type = data['types'][1]['type']['name'] if len(data['types']) > 1 else None
        hp = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        defense = data['stats'][2]['base_stat']
        special_attack = data['stats'][3]['base_stat']
        special_defense = data['stats'][4]['base_stat']
        speed = data['stats'][5]['base_stat']
        base_stat_total = sum(stat['base_stat'] for stat in data['stats'])

        stats = {
            'HP': hp,
            'Attack': attack,
            'Defense': defense,
            'Special Attack': special_attack,
            'Special Defense': special_defense,
            'Speed': speed,
        }

        pokemon_info = {
            'Species': species,
            'Primary Type': primary_type,
            'Secondary Type': secondary_type,
            'Stats': stats,
            'BST': base_stat_total,
        }

        if species.lower() in map(str.lower, static_types.type_swaps.keys()):
            pokemon_info['Primary Type'] = static_types.type_swaps[species]['primary_type']
            pokemon_info['Secondary Type'] = static_types.type_swaps[species]['secondary_type']

        if species.lower() in map(str.lower, static_types.type_overrides.keys()):
            pokemon_info['Primary Type'] = static_types.type_overrides[species]
            pokemon_info['Secondary Type'] = None

        return pokemon_info
    else:
        return None


def fuse_pokemon(pokemon1, pokemon2):
    stats_to_fuse = ['HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']

    fusion_1 = {
        'head': pokemon1['Species'],
        'body': pokemon2['Species'],
        'primary_type': pokemon1['Primary Type'],
        'secondary_type': pokemon2['Secondary Type'] if pokemon2['Secondary Type'] and pokemon2['Secondary Type'] != pokemon1['Primary Type'] else pokemon2['Primary Type'],
    }

    if pokemon1['Secondary Type'] != pokemon2['Primary Type']:
        fusion_2 = {
            'head': pokemon2['Species'],
            'body': pokemon1['Species'],
            'primary_type': pokemon2['Primary Type'],
            'secondary_type': pokemon1['Secondary Type'] if pokemon1['Secondary Type'] else pokemon1['Primary Type'],
        }
    else:
        fusion_2 = {
            'head': pokemon2['Species'],
            'body': pokemon1['Species'],
            'primary_type': pokemon2['Primary Type'],
            'secondary_type': pokemon1['Primary Type'],
        }

    fused_pokemon = [fusion_1, fusion_2]

    for fusion in fused_pokemon:
        fusion_stats = {}

        if fusion['head'] == pokemon1['Species']:
            head = pokemon1
            body = pokemon2
        else:
            head = pokemon2
            body = pokemon1

        for current_stat in stats_to_fuse:
            head_stat = head['Stats'][current_stat]
            body_stat = body['Stats'][current_stat]

            if current_stat in ['Attack', 'Defense', 'Speed']:
                fusion_stats[current_stat] = int((2 * body_stat / 3) + (head_stat / 3))
            else:
                fusion_stats[current_stat] = int((2 * head_stat / 3) + (body_stat / 3))

        base_stat_total = sum(fusion_stats.values())

        fusion['Stats'] = fusion_stats
        fusion['BST'] = base_stat_total

        # Check that we don't have duplicate types
        if fusion['primary_type'] == fusion['secondary_type']:
            fusion['secondary_type'] = None

    return fused_pokemon


def analyze_single_type(input_pokemon, adjust_for_threat_score: bool):
    type_data = get_type_data(input_pokemon['primary_type'].lower())

    resistances = {entry['name'] for entry in type_data['damage_relations']['half_damage_from']}
    immunities = {entry['name'] for entry in type_data['damage_relations']['no_damage_from']}
    weaknesses = {entry['name'] for entry in type_data['damage_relations']['double_damage_from']}

    # Here we enumerate if adjusting for threat score
    if adjust_for_threat_score:
        # Open the JSON file for reading
        file = open('fusion_dashboard/data/threat_scores.json')
        threat_scores = json.load(file)
        file.close()

        adjusted_weaknesses = 0
        adjusted_resistances = 0
        adjusted_immunities = 0

        for current_type in weaknesses:
            adjusted_weaknesses += threat_scores[current_type]

        for current_type in resistances:
            adjusted_resistances += threat_scores[current_type]

        for current_type in immunities:
            adjusted_immunities += threat_scores[current_type]

        effective_delta = adjusted_resistances + (adjusted_immunities * 2) - adjusted_weaknesses
    else:
        # alt calculation here - immunities should count for 2
        effective_delta = (len(resistances) + (len(immunities) * 2)) - len(weaknesses)

    input_pokemon['Normal_Resistances'] = resistances
    input_pokemon['Super_Resistances'] = None
    input_pokemon['Immunities'] = immunities
    input_pokemon['Normal_Weaknesses'] = weaknesses
    input_pokemon['Super_Weaknesses'] = None
    input_pokemon['Total_resistances'] = len(resistances)
    input_pokemon['Total_weaknesses'] = len(weaknesses)
    input_pokemon['Effective_delta'] = effective_delta

    return input_pokemon


def analyze_resistances(input_pokemon, adjust_for_threat_score: bool):
    type1, type2 = input_pokemon['primary_type'].lower(), input_pokemon['secondary_type'].lower()

    type1_data = get_type_data(type1)
    type2_data = get_type_data(type2)

    resistances1 = {entry['name'] for entry in type1_data['damage_relations']['half_damage_from']}
    resistances2 = {entry['name'] for entry in type2_data['damage_relations']['half_damage_from']}

    immunities1 = {entry['name'] for entry in type1_data['damage_relations']['no_damage_from']}
    immunities2 = {entry['name'] for entry in type2_data['damage_relations']['no_damage_from']}

    weaknesses1 = {entry['name'] for entry in type1_data['damage_relations']['double_damage_from']}
    weaknesses2 = {entry['name'] for entry in type2_data['damage_relations']['double_damage_from']}

    combined_resistances = resistances1.union(resistances2)
    combined_weaknesses = weaknesses1.union(weaknesses2)
    combined_immunities = immunities1.union(immunities2)

    super_resisted_types = resistances1.intersection(resistances2)
    super_weak_types = weaknesses1.intersection(weaknesses2)

    resisted_types = combined_resistances - combined_weaknesses
    resisted_types = resisted_types - super_resisted_types
    resisted_types = resisted_types - combined_immunities

    combined_weaknesses = combined_weaknesses - combined_resistances
    combined_weaknesses = combined_weaknesses - combined_immunities
    combined_weaknesses = combined_weaknesses - super_resisted_types
    combined_weaknesses = combined_weaknesses - super_weak_types

    num_weak = len(combined_weaknesses) + len(super_weak_types)
    num_resist = len(resisted_types) + len(super_resisted_types) + len(combined_immunities)

    # Here we enumerate if adjusting for threat score
    if adjust_for_threat_score:
        # Open the JSON file for reading
        file = open('fusion_dashboard/data/threat_scores.json')
        threat_scores = json.load(file)
        file.close()

        adjusted_weaknesses = 0
        adjusted_super_weak = 0
        adjusted_resisted_types = 0
        adjusted_super_resisted_types = 0
        adjusted_combined_immunities = 0

        for current_type in combined_weaknesses:
            adjusted_weaknesses += threat_scores[current_type]

        for current_type in super_weak_types:
            adjusted_super_weak += threat_scores[current_type]

        for current_type in resisted_types:
            adjusted_resisted_types += threat_scores[current_type]

        for current_type in super_resisted_types:
            adjusted_super_resisted_types += threat_scores[current_type]

        for current_type in combined_immunities:
            adjusted_combined_immunities += threat_scores[current_type]

        delta_weak = adjusted_weaknesses + (adjusted_super_weak * 2)
        delta_resist = adjusted_resisted_types + adjusted_super_resisted_types + (adjusted_combined_immunities * 2)
    else:
        delta_weak = len(combined_weaknesses) + (len(super_weak_types) * 2)
        delta_resist = len(resisted_types) + len(super_resisted_types) + (len(combined_immunities) * 2)

    effective_delta = delta_resist - delta_weak

    input_pokemon['Normal_Resistances'] = resisted_types
    input_pokemon['Super_Resistances'] = super_resisted_types
    input_pokemon['Immunities'] = combined_immunities
    input_pokemon['Normal_Weaknesses'] = combined_weaknesses
    input_pokemon['Super_Weaknesses'] = super_weak_types
    input_pokemon['Total_resistances'] = num_resist
    input_pokemon['Total_weaknesses'] = num_weak
    input_pokemon['Effective_delta'] = effective_delta

    return input_pokemon


def find_extreme_score_pairs(pair_scores, find_max=True):
    def backtrack(elements, current_score, current_pairs):
        nonlocal extreme_score, extreme_pairs

        if not elements:
            if (find_max and current_score > extreme_score) or (not find_max and current_score < extreme_score):
                extreme_score = current_score
                extreme_pairs = current_pairs[:]
            return

        for pair in list(pair_scores.keys()):
            if pair[0] in elements and pair[1] in elements:
                remaining_elements = elements - set(pair)
                current_pairs.append(pair)
                current_score += pair_scores[pair]
                backtrack(remaining_elements, current_score, current_pairs)
                current_pairs.pop()
                current_score -= pair_scores[pair]

    extreme_score = float('-inf') if find_max else float('inf')
    extreme_pairs = []
    all_elements = {element for pair in pair_scores.keys() for element in pair}

    backtrack(all_elements, 0, [])

    return extreme_pairs


def transform_dataframe_to_weighted_pairs(df, weight_field):
    pair_scores = {}

    for _, row in df.iterrows():
        head, body, score = row['Head'], row['Body'], row[weight_field]
        pair = (head, body)
        pair_scores[pair] = score

    return pair_scores


@st.cache_data
def get_possible_fusions(pokemon_list, adjust_for_threat_score):
    analyzed_pokemon = []

    for current_name in pokemon_list:
        analyzed_pokemon.append(get_pokemon_info(current_name.lower()))

    possible_fusions = []

    for i in range(len(analyzed_pokemon)):
        for j in range(i + 1, len(analyzed_pokemon)):
            pokemon1 = analyzed_pokemon[i]
            pokemon2 = analyzed_pokemon[j]

            # Send the pair to the function
            fused_pair = fuse_pokemon(pokemon1, pokemon2)
            for current_fusion in fused_pair:
                possible_fusions.append(current_fusion)

    analyzed_fusions = []

    for combination in possible_fusions:
        # ('Charizard', 'Blastoise', 'fire', 'water')
        # here handle single type Pokemon, e.g. 'water', 'water'
        if not combination['secondary_type']:
            single_type_pokemon = analyze_single_type(combination, adjust_for_threat_score)
            analyzed_fusions.append(single_type_pokemon)
        else:
            fused = analyze_resistances(combination, adjust_for_threat_score)
            analyzed_fusions.append(fused)

    # Sort the list by effective delta, descending
    analyzed_fusions = sorted(analyzed_fusions, key=lambda x: x['Effective_delta'], reverse=True)

    output_df = get_pokemon_df(input_pokemon=analyzed_fusions)
    return output_df


@st.cache_data
def get_optimal_fusions(input_df, prioritized_metric):
    weighted_pairs = transform_dataframe_to_weighted_pairs(input_df, prioritized_metric)

    # Special handling for total weaknesses, lower is better
    if prioritized_metric == 'Total Weaknesses':
        optimal_pairs = find_extreme_score_pairs(weighted_pairs, find_max=False)
    else:
        optimal_pairs = find_extreme_score_pairs(weighted_pairs)

    # Extract matching records
    # Create a set of tuples from optimal_pairs for faster lookup
    optimal_set = set(optimal_pairs)

    # Filter the DataFrame to only rows where the (Head, Body) tuple is in optimal_set
    optimal_fusions = input_df[input_df[['Head', 'Body']].apply(tuple, axis=1).isin(optimal_set)]

    return optimal_fusions


@st.cache_data
def create_fused_team(pairs, adjust_for_threat_score):
    fused_team = []

    for pair in pairs:
        # Get data for each Pokémon
        pokemon1 = get_pokemon_info(pair[0].lower())
        pokemon2 = get_pokemon_info(pair[1].lower())

        # Send the pair to the function
        fused_pair = fuse_pokemon(pokemon1, pokemon2)

        for current_fusion in fused_pair:
            if current_fusion['head'] == pair[0].lower():
                fused_team.append(current_fusion)

    analyzed_fusions = []

    for combination in fused_team:
        # ('Charizard', 'Blastoise', 'fire', 'water')
        # here handle single type Pokemon, e.g. 'water', 'water'
        if not combination['secondary_type']:
            single_type_pokemon = analyze_single_type(combination, adjust_for_threat_score)
            analyzed_fusions.append(single_type_pokemon)
        else:
            fused = analyze_resistances(combination, adjust_for_threat_score)
            analyzed_fusions.append(fused)

    # Sort the list by effective delta, descending
    analyzed_fusions = sorted(analyzed_fusions, key=lambda x: x['Effective_delta'], reverse=True)

    team_df = get_pokemon_df(input_pokemon=analyzed_fusions)

    return team_df
