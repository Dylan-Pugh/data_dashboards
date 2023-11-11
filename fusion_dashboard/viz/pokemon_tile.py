import pandas as pd
import streamlit as st
from viz.display_functions import display_sprite_with_fallback


@st.cache_data
def st_pokemon_tile(pokemon_df):
    with st.expander(label=f'{pokemon_df["Head"].capitalize()}/{pokemon_df["Body"].capitalize()}'):
        # Display the Pokemon image
        display_sprite_with_fallback(
            head_pokedex_number=pokemon_df['Head Id'],
            body_pokedex_number=pokemon_df['Body Id'],
        )

        # Display the Pokemon details
        if pokemon_df['Secondary Type']:
            st.markdown(f'**Type:** {pokemon_df["Primary Type"].capitalize()}/{pokemon_df["Secondary Type"].capitalize()}')
        else:
            st.markdown(f'**Type:** {pokemon_df["Primary Type"].capitalize()}')

        st.markdown(f'**BST:** {pokemon_df["Bst"]}')

        # Level selector
        current_level = st.number_input(
            label='Current Level',
            value=20,
            min_value=1,
            max_value=100,
            key=f'{pokemon_df["Head"].capitalize()}/{pokemon_df["Body"].capitalize()}_level_select',
        )

        st.markdown('**Upcoming Moves:**')

        # Handle learnsets
        learnset = pokemon_df['Learnset']

        # Filter so we only see upcoming moves
        filtered_dict = {key: value for key, value in learnset.items() if isinstance(key, int) and key > current_level}

        # Enumerate the dict
        enumerated_data = [(key, value) for key, value in filtered_dict.items()]

        # Create a DataFrame from the list
        learnset_df = pd.DataFrame(enumerated_data, columns=['Level', 'Move'])

        # Sort by level
        learnset_df = learnset_df.sort_values(by='Level', ascending=True)
        st.dataframe(data=learnset_df, use_container_width=True, hide_index=True)

        # Display Evoline
        st.markdown('**Upcoming Evolutions:**')

        evoline = pokemon_df['Evoline']

        # Filter so we only see upcoming evos
        filtered_evo_levels = {}
        other_evo_methods = {}

        for key, value in evoline.items():
            if isinstance(key, str):
                other_evo_methods[key] = value
            elif isinstance(key, int) and key > 90:
                # This is to account for happiness scores
                other_evo_methods[key] = value
            else:
                filtered_evo_levels[key] = value

        # Enumerate the dicts
        if filtered_evo_levels:
            enumerated_levels = [(key, value) for key, value in filtered_evo_levels.items()]

            # Create a DataFrame from the list
            evoline_df = pd.DataFrame(enumerated_levels, columns=['Level', 'Evolution'])

            # Sort by level
            evoline_df = evoline_df.sort_values(by='Level', ascending=True)

            # Display both
            st.dataframe(data=evoline_df, use_container_width=True, hide_index=True)

        if other_evo_methods:
            enumerated_methods = [(key, value) for key, value in other_evo_methods.items()]
            other_method_df = pd.DataFrame(enumerated_methods, columns=['Item/Happiness', 'Evolution'])
            st.dataframe(data=other_method_df, use_container_width=True, hide_index=True)

        # Display move set selector
        unpacked_moves = [move.capitalize() for sublist in learnset.values() if isinstance(sublist, list) for move in sublist]
        st.multiselect(
            label='Moveset',
            options=unpacked_moves,
            max_selections=4,
            key=f'{pokemon_df["Head"].capitalize()}/{pokemon_df["Body"].capitalize()}_move_select',
        )
