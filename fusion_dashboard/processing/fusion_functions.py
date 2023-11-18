import json
import pandas as pd
import requests
import streamlit as st
from data import constants, static_swaps


@st.cache_data
def get_species_dex_dict():
    df = pd.read_csv('fusion_dashboard/data/current_dex.csv')
    return df.set_index('NAME')['ID'].to_dict()


@st.cache_data
def get_pokemon_df(input_pokemon) -> pd.DataFrame:
    # Preprocess the input data
    for entry in input_pokemon:
        # Remove curly braces from sets and convert to comma-separated strings
        for key, value in entry.items():
            if isinstance(value, set):
                entry[key] = ', '.join(value)

    # Define the desired column order and rename columns
    column_order = [
        'ID',
        'head',
        'head_ID',
        'body',
        'body_ID',
        'primary_type',
        'secondary_type',
        'HP',
        'Attack',
        'Defense',
        'Special Attack',
        'Special Defense',
        'Speed',
        'BST',
        'Effective_delta',
        'Normal_Resistances',
        'Super_Resistances',
        'Immunities',
        'Neutral_Types',
        'Normal_Weaknesses',
        'Super_Weaknesses',
        'Total_resistances',
        'Total_weaknesses',
        'Learnset',
        'Evoline',
        'Current_Level',
        'Moveset',
        'Double_damage_to',
        'Neutral_damage_to',
        'Half_damage_to',
        'No_damage_to',
    ]

    # Create a Pandas DataFrame from the list of dictionaries with reordered columns and renamed columns
    df = pd.DataFrame(input_pokemon, columns=column_order)

    # Normalize column names (replace underscores with spaces and capitalize each word)
    df.columns = [col.replace('_', ' ').title() for col in df.columns]

    # Rename special columns
    df.rename(
        columns={
            'Id': 'ID',
            'Head Id': 'Head ID',
            'Body Id': 'Body ID',
            'Hp': 'HP',
            'Bst': 'BST',
        },
        inplace=True,
    )

    df.to_csv(
        path_or_buf='fusion_dashboard/data/current_team.csv',
        index=False,
    )
    return df


def get_team_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def get_type_data(type_name):
    response = requests.get(f'https://pokeapi.co/api/v2/type/{type_name}')
    type_data = response.json()
    return type_data


@st.cache_data
def get_move_data(move_name):
    # PokeAPI URL for move details
    url = f'https://pokeapi.co/api/v2/move/{move_name}/'

    try:
        # Send a GET request to the API
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            move_data = response.json()
            move_type = move_data['type']['name']
            move_power = move_data['power'] if 'power' in move_data else None
            return move_type, move_power
        else:
            return None, None

    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        return None, None


@st.cache_data
def analyze_moveset(moves_list):
    # Create an empty DataFrame to store move details
    move_details = []

    # Iterate through the list of moves
    for move in moves_list:
        move_type, move_power = get_move_data(move)
        move_details.append(
            {
                'Move': move,
                'Type': move_type,
                'Power': move_power,
            },
        )

    # Create a DataFrame from the list of move details
    move_details_df = pd.DataFrame(move_details)

    # Add a 'Caution' column based on the 'Power' column and the 'dangerous_moves' list
    move_details_df['Caution'] = (move_details_df['Power'] >= 80) | (
        move_details_df['Move'].isin(constants.DANGEROUS_MOVES)
    )

    move_details_df['Move'] = move_details_df['Move'].str.capitalize()
    move_details_df['Type'] = move_details_df['Type'].str.capitalize()
    move_details_df['Power'] = move_details_df['Power'].fillna(0).astype(int)

    return move_details_df


@st.cache_data
def extract_learnset(moves_dict: dict):
    # Initialize an empty result dictionary
    result_dict = {}

    # Loop through each move object in the list
    for move_data in moves_dict:
        move_name = move_data['move']['name']

        # Loop through the 'version_group_details' list for the current move object
        for item in move_data['version_group_details']:
            if item['version_group']['name'] == 'ultra-sun-ultra-moon':
                level_learned_at = None
                if item['move_learn_method']['name'] == 'level-up':
                    level_learned_at = item['level_learned_at']
                elif item['move_learn_method']['name'] == 'machine':
                    level_learned_at = 'TM'

                if level_learned_at:
                    if level_learned_at in result_dict.keys():
                        result_dict[level_learned_at].append(move_name)
                    else:
                        result_dict[level_learned_at] = [move_name]

    return result_dict


@st.cache_data
def combine_learnsets(learnset1, learnset2):
    """
    Combine two learnsets, keeping unique move IDs and concatenating move names for duplicate move IDs.

    Args:
        learnset1 (dict): The first learnset dictionary.
        learnset2 (dict): The second learnset dictionary.

    Returns:
        dict: A combined learnset dictionary.
    """
    # Create a copy of learnset1 to avoid modifying the original dictionary
    combined_learnset = learnset1.copy()

    # Iterate through the second learnset (learnset2)
    for learn_level, move_list in learnset2.items():
        # If the move ID is already in combined_learnset, append the move name
        if learn_level in combined_learnset:
            combined_learnset[learn_level] += move_list
        # Otherwise, add the move ID and move name to combined_learnset
        else:
            combined_learnset[learn_level] = move_list

    return combined_learnset


@st.cache_data
def get_evolution_levels(pokemon_name):
    # Step 1: Send an HTTP GET request to retrieve species information
    species_url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}'
    species_response = requests.get(species_url)

    if species_response.status_code != 200:
        return None  # Failed to get species information

    species_data = species_response.json()

    # Step 2: Extract the URL of the evolution chain
    evolution_chain_url = species_data['evolution_chain']['url']

    # Step 3: Send an HTTP GET request to the evolution chain URL
    evolution_chain_response = requests.get(evolution_chain_url)

    if evolution_chain_response.status_code != 200:
        return None  # Failed to get evolution chain information

    evolution_chain_data = evolution_chain_response.json()

    # Step 4: Extract the evolution details

    evolution_details = {}
    current = evolution_chain_data['chain']

    while current:
        if 'evolves_to' in current and len(current['evolves_to']) > 0:
            for evolution in current['evolves_to']:
                evo_data = evolution['evolution_details'][0]
                result = next(
                    (
                        v
                        for v in evo_data.values()
                        if v or (isinstance(v, dict) and (v.get('name')))
                    ),
                    None,
                )
                if result:
                    species = evolution['species']['name'].capitalize()

                    if species in static_swaps.evo_overrides.keys():
                        result = static_swaps.evo_overrides[species]

                    if isinstance(result, dict):
                        result = result['name'].capitalize()

                    if isinstance(result, (int, str)):
                        result = [result]

                    for result in result:
                        if result in evolution_details:
                            evolution_details[result].append(species)
                        else:
                            evolution_details[result] = [species]

                current = evolution
        else:
            break

    return evolution_details


@st.cache_data
def get_pokemon_info(pokemon_name):
    # Account for form differences here, move to constant in the future
    if pokemon_name == 'aegislash':
        pokemon_name = 'aegislash-blade'
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        species = data['species']['name']
        primary_type = data['types'][0]['type']['name']
        secondary_type = (
            data['types'][1]['type']['name'] if len(data['types']) > 1 else None
        )
        HP = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        defense = data['stats'][2]['base_stat']
        special_attack = data['stats'][3]['base_stat']
        special_defense = data['stats'][4]['base_stat']
        speed = data['stats'][5]['base_stat']
        base_stat_total = sum(stat['base_stat'] for stat in data['stats'])

        # override for all Normal/Flying types
        if primary_type == 'normal' and secondary_type == 'flying':
            primary_type = 'flying'
            secondary_type = None

        species_dex_lookup = get_species_dex_dict()

        pokemon_info = {
            'Species': species,
            'ID': species_dex_lookup[species],
            'Primary Type': primary_type,
            'Secondary Type': secondary_type,
            'HP': HP,
            'Attack': attack,
            'Defense': defense,
            'Special Attack': special_attack,
            'Special Defense': special_defense,
            'Speed': speed,
            'BST': base_stat_total,
            'Learnset': extract_learnset(data['moves']),
            'Evoline': get_evolution_levels(species),
        }

        if species.lower() in map(str.lower, static_swaps.type_swaps.keys()):
            pokemon_info['Primary Type'] = static_swaps.type_swaps[species][
                'primary_type'
            ]
            pokemon_info['Secondary Type'] = static_swaps.type_swaps[species][
                'secondary_type'
            ]

        if species.lower() in map(str.lower, static_swaps.type_overrides.keys()):
            pokemon_info['Primary Type'] = static_swaps.type_overrides[species]
            pokemon_info['Secondary Type'] = None

        return pokemon_info
    else:
        return None


@st.cache_data
def fuse_pokemon(pokemon1, pokemon2):
    stats_to_fuse = [
        'HP',
        'Attack',
        'Defense',
        'Special Attack',
        'Special Defense',
        'Speed',
    ]

    fusion_1 = {
        'head': pokemon1['Species'],
        'body': pokemon2['Species'],
        'ID': float(f"{pokemon1['ID']}.{pokemon2['ID']}"),
        'head_ID': pokemon1['ID'],
        'body_ID': pokemon2['ID'],
        'primary_type': pokemon1['Primary Type'],
        'secondary_type': pokemon2['Secondary Type']
        if pokemon2['Secondary Type']
        and pokemon2['Secondary Type'] != pokemon1['Primary Type']
        else pokemon2['Primary Type'],
    }

    if pokemon1['Secondary Type'] != pokemon2['Primary Type']:
        fusion_2 = {
            'head': pokemon2['Species'],
            'body': pokemon1['Species'],
            'ID': float(f"{pokemon2['ID']}.{pokemon1['ID']}"),
            'head_ID': pokemon2['ID'],
            'body_ID': pokemon1['ID'],
            'primary_type': pokemon2['Primary Type'],
            'secondary_type': pokemon1['Secondary Type']
            if pokemon1['Secondary Type']
            else pokemon1['Primary Type'],
        }
    else:
        fusion_2 = {
            'head': pokemon2['Species'],
            'body': pokemon1['Species'],
            'ID': float(f"{pokemon2['ID']}.{pokemon1['ID']}"),
            'head_ID': pokemon2['ID'],
            'body_ID': pokemon1['ID'],
            'primary_type': pokemon2['Primary Type'],
            'secondary_type': pokemon1['Primary Type'],
        }

    # Both possible fusions will have the same learnset & evolines
    combined_learnset = combine_learnsets(pokemon1['Learnset'], pokemon2['Learnset'])
    combined_evo_lines = combine_learnsets(pokemon1['Evoline'], pokemon2['Evoline'])

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
            head_stat = head[current_stat]
            body_stat = body[current_stat]

            if current_stat in ['Attack', 'Defense', 'Speed']:
                fusion_stats[current_stat] = int((2 * body_stat / 3) + (head_stat / 3))
            else:
                fusion_stats[current_stat] = int((2 * head_stat / 3) + (body_stat / 3))

        for current_stat in fusion_stats.keys():
            fusion[current_stat] = fusion_stats[current_stat]

        base_stat_total = sum(fusion_stats.values())

        fusion['BST'] = base_stat_total

        # Check that we don't have duplicate types
        if fusion['primary_type'] == fusion['secondary_type']:
            fusion['secondary_type'] = None

        # Add combined learnset
        fusion['Learnset'] = combined_learnset

        # Add combined evoline
        fusion['Evoline'] = combined_evo_lines

    return fused_pokemon


@st.cache_data
def get_type_coverage(input_moves: list[str]):
    input_move_types = set()
    for current_move in set(input_moves):
        type, power = get_move_data(current_move.lower())
        if power:
            input_move_types.add(type)

    covered_types = set()
    resisted_types = set()
    immune_types = set()
    neutral_types = set()

    all_types = {i.lower() for i in constants.TYPES}

    for offensive_type in input_move_types:
        # Get damage relations
        damage_relations = get_type_data(offensive_type)['damage_relations']

        double_damage_to = [
            item['name'] for item in damage_relations['double_damage_to']
        ]
        half_damage_to = [item['name'] for item in damage_relations['half_damage_to']]
        no_damage_to = [item['name'] for item in damage_relations['no_damage_to']]

        for defensive_type in all_types:
            if defensive_type in double_damage_to:
                covered_types.add(defensive_type)
            elif (
                defensive_type in half_damage_to
                and defensive_type not in covered_types
                and defensive_type not in neutral_types
            ):
                resisted_types.add(defensive_type)
            elif (
                defensive_type in no_damage_to
                and defensive_type not in covered_types
                and defensive_type not in neutral_types
                and defensive_type not in resisted_types
            ):
                immune_types.add(defensive_type)
            elif (
                defensive_type not in neutral_types
                and defensive_type not in covered_types
            ):
                neutral_types.add(defensive_type)

        neutral_types -= covered_types

        resisted_types -= covered_types
        resisted_types -= neutral_types

        immune_types -= covered_types
        immune_types -= neutral_types
        immune_types -= resisted_types

    # return dict
    moveset_damage_relations = {
        'double_damage_to': list(covered_types),
        'neutral_damage_to': list(neutral_types),
        'half_damage_to': list(resisted_types),
        'no_damage_to': list(immune_types),
    }
    return moveset_damage_relations


@st.cache_data
def analyze_single_type(input_pokemon, adjust_for_threat_score: bool):
    type_data = get_type_data(input_pokemon['primary_type'].lower())

    resistances = {
        entry['name'] for entry in type_data['damage_relations']['half_damage_from']
    }
    immunities = {
        entry['name'] for entry in type_data['damage_relations']['no_damage_from']
    }
    weaknesses = {
        entry['name'] for entry in type_data['damage_relations']['double_damage_from']
    }

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

        effective_delta = (
            adjusted_resistances + (adjusted_immunities * 2) - adjusted_weaknesses
        )
    else:
        # alt calculation here - immunities should count for 2
        effective_delta = (len(resistances) + (len(immunities) * 2)) - len(weaknesses)

    # Add in neutral types
    neutral_types = [
        type.lower()
        for type in constants.TYPES
        if type.lower() not in (resistances | immunities | weaknesses)
    ]

    input_pokemon['Normal_Resistances'] = resistances
    input_pokemon['Immunities'] = immunities
    input_pokemon['Neutral_Types'] = set(neutral_types)
    input_pokemon['Normal_Weaknesses'] = weaknesses
    input_pokemon['Super_Weaknesses'] = set()
    input_pokemon['Total_resistances'] = len(resistances)
    input_pokemon['Super_Resistances'] = set()
    input_pokemon['Total_weaknesses'] = len(weaknesses)
    input_pokemon['Effective_delta'] = effective_delta

    return input_pokemon


@st.cache_data
def analyze_resistances(input_pokemon, adjust_for_threat_score: bool):
    type1, type2 = (
        input_pokemon['primary_type'].lower(),
        input_pokemon['secondary_type'].lower(),
    )

    type1_data = get_type_data(type1)
    type2_data = get_type_data(type2)

    resistances1 = {
        entry['name'] for entry in type1_data['damage_relations']['half_damage_from']
    }
    resistances2 = {
        entry['name'] for entry in type2_data['damage_relations']['half_damage_from']
    }

    immunities1 = {
        entry['name'] for entry in type1_data['damage_relations']['no_damage_from']
    }
    immunities2 = {
        entry['name'] for entry in type2_data['damage_relations']['no_damage_from']
    }

    weaknesses1 = {
        entry['name'] for entry in type1_data['damage_relations']['double_damage_from']
    }
    weaknesses2 = {
        entry['name'] for entry in type2_data['damage_relations']['double_damage_from']
    }

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
    num_resist = (
        len(resisted_types) + len(super_resisted_types) + len(combined_immunities)
    )

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
        delta_resist = (
            adjusted_resisted_types
            + adjusted_super_resisted_types
            + (adjusted_combined_immunities * 2)
        )
    else:
        delta_weak = len(combined_weaknesses) + (len(super_weak_types) * 2)
        delta_resist = (
            len(resisted_types)
            + len(super_resisted_types)
            + (len(combined_immunities) * 2)
        )

    effective_delta = delta_resist - delta_weak

    # Add in neutral types
    neutral_types = [
        type.lower()
        for type in constants.TYPES
        if type.lower()
        not in (
            resisted_types
            | super_resisted_types
            | combined_immunities
            | combined_weaknesses
            | super_weak_types
        )
    ]

    input_pokemon['Normal_Resistances'] = resisted_types
    input_pokemon['Super_Resistances'] = super_resisted_types
    input_pokemon['Immunities'] = combined_immunities
    input_pokemon['Neutral_Types'] = set(neutral_types)
    input_pokemon['Normal_Weaknesses'] = combined_weaknesses
    input_pokemon['Super_Weaknesses'] = super_weak_types
    input_pokemon['Total_resistances'] = num_resist
    input_pokemon['Total_weaknesses'] = num_weak
    input_pokemon['Effective_delta'] = effective_delta

    return input_pokemon


@st.cache_data
def find_extreme_score_pairs(pair_scores, find_max=True):
    def backtrack(elements, current_score, current_pairs):
        nonlocal extreme_score, extreme_pairs

        if not elements or len(elements) <= 1:
            if (find_max and current_score > extreme_score) or (
                not find_max and current_score < extreme_score
            ):
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


@st.cache_data
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
            single_type_pokemon = analyze_single_type(
                combination, adjust_for_threat_score,
            )
            analyzed_fusions.append(single_type_pokemon)
        else:
            fused = analyze_resistances(combination, adjust_for_threat_score)
            analyzed_fusions.append(fused)

    # Sort the list by effective delta, descending
    analyzed_fusions = sorted(
        analyzed_fusions, key=lambda x: x['Effective_delta'], reverse=True,
    )

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
    optimal_fusions = input_df[
        input_df[['Head', 'Body']].apply(tuple, axis=1).isin(optimal_set)
    ]

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
            single_type_pokemon = analyze_single_type(
                combination, adjust_for_threat_score,
            )
            analyzed_fusions.append(single_type_pokemon)
        else:
            fused = analyze_resistances(combination, adjust_for_threat_score)
            analyzed_fusions.append(fused)

    # Create special 'team' entry
    keys_to_sum = [
                   'HP',
                   'Attack',
                   'Defense',
                   'Special Attack',
                   'Special Defense',
                   'Speed',
                   'BST',
                   'Total_resistances',
                   'Total_weaknesses',
                   'Effective_delta',
    ]

    team_totals = {key: sum(d[key] for d in analyzed_fusions) for key in keys_to_sum}

    team_totals['ID'] = 0
    team_totals['Normal_Resistances'] = set()
    team_totals['Super_Resistances'] = set()
    team_totals['Immunities'] = set()
    team_totals['Neutral_Types'] = set()
    team_totals['Normal_Weaknesses'] = set()
    team_totals['Super_Weaknesses'] = set()

    for fusion in analyzed_fusions:
        team_totals['Normal_Resistances'].update(fusion['Normal_Resistances'])
        team_totals['Super_Resistances'].update(fusion['Super_Resistances'])
        team_totals['Immunities'].update(fusion['Immunities'])
        team_totals['Neutral_Types'].update(fusion['Neutral_Types'])
        team_totals['Normal_Weaknesses'].update(fusion['Normal_Weaknesses'])
        team_totals['Super_Weaknesses'].update(fusion['Super_Weaknesses'])

    running_total = set()
    running_total.update(team_totals['Immunities'])

    team_totals['Super_Resistances'] = team_totals['Super_Resistances'] - running_total
    running_total.update(team_totals['Super_Resistances'])

    team_totals['Normal_Resistances'] = team_totals['Normal_Resistances'] - running_total
    running_total.update(team_totals['Normal_Resistances'])

    team_totals['Neutral_Types'] = team_totals['Neutral_Types'] - running_total
    running_total.update(team_totals['Neutral_Types'])

    team_totals['Normal_Weaknesses'] = team_totals['Normal_Weaknesses'] - running_total
    running_total.update(team_totals['Normal_Weaknesses'])

    team_totals['Super_Weaknesses'] = team_totals['Super_Weaknesses'] - running_total

    analyzed_fusions.append(team_totals)
    # Sort the list by effective delta, descending
    analyzed_fusions = sorted(
        analyzed_fusions, key=lambda x: x['Effective_delta'], reverse=True,
    )

    team_df = get_pokemon_df(input_pokemon=analyzed_fusions)

    return team_df


@st.cache_data
def calc_team_coverage(team_df: pd.DataFrame):
    combined_moveset = []
    team_index = 0

    for index, pokemon in team_df.iterrows():
        if pokemon['ID'] == 0:
            team_index = index
            continue

        level_key = f"{pokemon['ID']}_level_select"
        moveset_key = f"{pokemon['ID']}_move_select"

        if level_key in st.session_state:
            current_level = st.session_state[level_key]
            team_df.at[index, 'Current Level'] = current_level

        if moveset_key in st.session_state:
            current_moveset = st.session_state[moveset_key]

            mon_coverage = get_type_coverage(current_moveset)
            combined_moveset += current_moveset

            # Parse out moveset coverage
            for key, value in mon_coverage.items():
                modified_key = key.replace('_', ' ').title()
                team_df.at[index, modified_key] = ', '.join(value)

            team_df.at[index, 'Moveset'] = ', '.join(current_moveset)

    # Add in combined moveset for team coverage
    team_coverage = get_type_coverage(combined_moveset)

    # Parse out moveset coverage
    for key, value in team_coverage.items():
        modified_key = key.replace('_', ' ').title()
        team_df.at[team_index, modified_key] = ', '.join(value)

    st.session_state['current_team'] = team_df
