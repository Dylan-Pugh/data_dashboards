"""
Module to calculate offensive threat score.
Functions:

calculate_composite_offensive_threat_score: Calculates a weighted composite score
for the offensive threat posed by a pokemon team against opponents of each type.
"""


def calculate_composite_offensive_threat_score(offensive_potentials, weights):
    if weights is None:
        weights = {
            'Super_Effective_Count': 1,
            'Resisted_Count': 1,
            'Move_Count': 1,
            'Average_Power': 1,
            'Pokemon_with_Moves_Count': 1,
            'Pokemon_with_STAB': 1,
            'Average_Attack': 1,
            'Average_Special_Attack': 1,
            'STAB_Average_Attack': 1,
            'STAB_Average_Special_Attack': 1,
        }

    min_max_scaling = {}

    # Initialize min_max_scaling with default values
    for metric in offensive_potentials['normal']:
        min_max_scaling[metric] = (float('inf'), float('-inf'))

    # Loop through each type and update min_max_scaling
    for type_metrics in offensive_potentials.values():
        for metric, value in type_metrics.items():
            min_value, max_value = min_max_scaling[metric]
            min_value = min(min_value, value)
            max_value = max(max_value, value)
            min_max_scaling[metric] = (min_value, max_value)

    sorted_potentials = {}

    for type_name, offensive_metrics in offensive_potentials.items():
        # Normalize the metrics
        normalized_metrics = {}
        normalized_metrics['Super_Effective_Count'] = offensive_metrics['Super_Effective_Count'] / 18
        # Inverse relationship for Resisted_Count
        normalized_metrics['Resisted_Count'] = 1 - (offensive_metrics['Resisted_Count'] / 18)
        normalized_metrics['Move_Count'] = (offensive_metrics['Move_Count'] - min_max_scaling['Move_Count'][0]) / (min_max_scaling['Move_Count'][1] - min_max_scaling['Move_Count'][0])
        normalized_metrics['Average_Power'] = (offensive_metrics['Average_Power'] - min_max_scaling['Average_Power'][0]) / (min_max_scaling['Average_Power'][1] - min_max_scaling['Average_Power'][0])
        normalized_metrics['Pokemon_with_Moves_Count'] = (offensive_metrics['Pokemon_with_Moves_Count'] - min_max_scaling['Pokemon_with_Moves_Count'][0]) / (min_max_scaling['Pokemon_with_Moves_Count'][1] - min_max_scaling['Pokemon_with_Moves_Count'][0])
        normalized_metrics['Pokemon_with_STAB'] = (offensive_metrics['Pokemon_with_STAB'] - min_max_scaling['Pokemon_with_STAB'][0]) / (min_max_scaling['Pokemon_with_STAB'][1] - min_max_scaling['Pokemon_with_STAB'][0])
        normalized_metrics['Average_Attack'] = (offensive_metrics['Average_Attack'] - min_max_scaling['Average_Attack'][0]) / (min_max_scaling['Average_Attack'][1] - min_max_scaling['Average_Attack'][0])
        normalized_metrics['Average_Special_Attack'] = (offensive_metrics['Average_Special_Attack'] - min_max_scaling['Average_Special_Attack'][0]) / (min_max_scaling['Average_Special_Attack'][1] - min_max_scaling['Average_Special_Attack'][0])
        normalized_metrics['STAB_Average_Attack'] = (offensive_metrics['STAB_Average_Attack'] - min_max_scaling['STAB_Average_Attack'][0]) / (min_max_scaling['STAB_Average_Attack'][1] - min_max_scaling['STAB_Average_Attack'][0])
        normalized_metrics['STAB_Average_Special_Attack'] = (offensive_metrics['STAB_Average_Special_Attack'] - min_max_scaling['STAB_Average_Special_Attack'][0]) / (min_max_scaling['STAB_Average_Special_Attack'][1] - min_max_scaling['STAB_Average_Special_Attack'][0])

        # Calculate the weighted sum of normalized metrics
        weighted_sum = sum(weights[metric] * normalized_metrics[metric] for metric in normalized_metrics)

        # Calculate the composite_offensive_threat_score
        composite_offensive_threat_score = weighted_sum / len(normalized_metrics)

        # Updated code
        composite_offensive_threat_score = composite_offensive_threat_score * (1.5 - 0.5) + 0.5

        sorted_potentials[type_name] = composite_offensive_threat_score

    return sorted_potentials
