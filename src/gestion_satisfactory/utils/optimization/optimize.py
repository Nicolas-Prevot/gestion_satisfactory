from typing import Tuple, Dict, List
import pandas as pd
import numpy as np
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus


def get_optimize_prod( df_recipes: pd.DataFrame,raw_items: List[str],raw_weights: Dict[str, float],raw_limits: Dict[str, float],not_raw_items: List[str],selected_products: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, str], str]:
    """
    Optimize the production of items based on recipes and constraints.

    Parameters
    ----------
    df_recipes : pd.DataFrame
        DataFrame containing recipe information.
    raw_items : list of str
        List of raw item names.
    raw_weights : dict
        Dictionary of weights for raw items used in the objective function.
    raw_limits : dict
        Dictionary of limits for raw items.
    not_raw_items : list of str
        List of non-raw item names.
    selected_products : dict
        Dictionary of desired production quantities for selected products.

    Returns
    -------
    Tuple[Dict[str, float], Dict[str, str], str]
        - recipe_vars: Dictionary mapping recipe variable names to their optimized amounts.
        - recipe_var_to_name: Dictionary mapping recipe variable names to recipe names.
        - status: Optimization status as a string.

    Notes
    -----
    The function formulates and solves a linear programming problem to find the optimal
    combination of recipes that meets the production targets while minimizing the use
    of raw materials according to their weights and limits.

    """
    df_recipes = df_recipes.copy().reset_index(drop=True)
    df_recipes['recipe'] = df_recipes.index

    # Prepare ingredients DataFrame
    ingredients_list = []
    for k in range(1, 5):
        df = df_recipes[['recipe', 'duration', f'ingredient_{k}', f'ingredient_amount_{k}']].copy()
        df.columns = ['recipe', 'duration', 'item', 'amount']
        df = df.dropna(subset=['item'])
        df['amount'] = - 60 * df['amount'] / df['duration']  # Negative since consumed; rate per minute
        ingredients_list.append(df)
    ingredients_long = pd.concat(ingredients_list, ignore_index=True)

    # Prepare products DataFrame
    products_list = []
    for k in range(1, 3):
        df = df_recipes[['recipe', 'duration', f'product_{k}', f'product_amount_{k}']].copy()
        df.columns = ['recipe', 'duration', 'item', 'amount']
        df = df.dropna(subset=['item'])
        df['amount'] = 60 * df['amount'] / df['duration']  # Positive since produced; rate per minute
        products_list.append(df)
    products_long = pd.concat(products_list, ignore_index=True)

    # Combine ingredients and products
    transactions = pd.concat([ingredients_long, products_long], ignore_index=True)

    # Group by item and recipe to get net amounts
    net_amounts = transactions.groupby(['item', 'recipe'])['amount'].sum().unstack(fill_value=0)

    recipes_idx = df_recipes['recipe'].tolist()
    R_items = list(not_raw_items)
    Rp_items = list(raw_items)

    # Ensure that all recipes are included in net_amounts columns
    net_amounts = net_amounts.reindex(columns=recipes_idx, fill_value=0)

    R = net_amounts.loc[R_items, recipes_idx].values if R_items else np.empty((0, len(recipes_idx)))
    Rp = net_amounts.loc[Rp_items, recipes_idx].values if Rp_items else np.empty((0, len(recipes_idx)))


    # Optimization Problem
    prob = LpProblem("combination_recipes", LpMinimize)
    Lmbda = LpVariable.dicts("Recipe", recipes_idx, cat='Continuous', lowBound=0)

    # Objective
    weight_values = np.array([raw_weights.get(item, 0) for item in Rp_items])
    prob += -lpSum([Lmbda[idx] * (Rp[:, idx] @ weight_values) for idx in recipes_idx])

    # Apply constraints for not_raw_items
    for i, item in enumerate(R_items):
        net_production = [R[i, idx - recipes_idx[0]] * Lmbda[idx] for idx in recipes_idx]
        if item in selected_products:
            prob += lpSum(net_production) == selected_products[item]
        else:
            prob += lpSum(net_production) >= 0

    # Apply constraints for raw_items
    for i, item in enumerate(Rp_items):
        net_production = [Rp[i, idx - recipes_idx[0]] * Lmbda[idx] for idx in recipes_idx]
        prob += lpSum(net_production) >= -raw_limits[item]

    # Solve the problem
    prob.solve()

    recipe_vars = {v.name: v.varValue for v in prob.variables()}
    recipe_var_to_name = {v.name: df_recipes.at[int(v.name.split("_")[-1]), "recipe_name"] for v in prob.variables()}
    status = LpStatus[prob.status]

    return recipe_vars, recipe_var_to_name, status
