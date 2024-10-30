from typing import Tuple, Dict, Set
import pandas as pd
import numpy as np
import re


def extract_tier(unlocked_by: str) -> int:
    """
    Extract the tier number from the 'unlocked_by' string.

    Parameters
    ----------
    unlocked_by : str
        String containing information about the unlock requirements.

    Returns
    -------
    int
        The tier number extracted from the string, or 0 if not found.

    """
    if pd.isnull(unlocked_by) or unlocked_by == "":
        return 0  # Default tier 0 for items without 'unlocked_by'
    match = re.search(r"Tier (\d+)", unlocked_by)
    if match:
        return int(match.group(1))
    else:
        return 0


def remove_uncraftable_rows(
    df_recipes: pd.DataFrame,
    raw_materials_1_: Dict[str, float],
    raw_materials_2_: Dict[str, float],
    raw_materials_limit_1_: Dict[str, float],
    raw_materials_limit_2_: Dict[str, float],
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], pd.DataFrame, Set[str]]:
    """
    Remove recipes that cannot be crafted due to missing ingredients.

    Parameters
    ----------
    df_recipes : pd.DataFrame
        DataFrame containing recipes.
    raw_materials_1_ : dict
        Dictionary of raw materials and their values (first category).
    raw_materials_2_ : dict
        Dictionary of raw materials and their values (second category).
    raw_materials_limit_1_ : dict
        Dictionary of limits for raw materials (first category).
    raw_materials_limit_2_ : dict
        Dictionary of limits for raw materials (second category).

    Returns
    -------
    Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], pd.DataFrame, Set[str]]
        Updated dictionaries of raw materials and limits, the updated DataFrame of recipes, and the set of uncraftable items.

    """
    ingredients = set(df_recipes[[f"ingredient_{k}" for k in range(1, 5)]].values.flatten()) - set([np.nan, None])

    raw_materials_1 = {item: value for item, value in raw_materials_1_.items() if item in ingredients}
    raw_materials_limit_1 = {item: value for item, value in raw_materials_limit_1_.items() if item in ingredients}
    raw_materials_2 = {item: value for item, value in raw_materials_2_.items() if item in ingredients}
    raw_materials_limit_2 = {item: value for item, value in raw_materials_limit_2_.items() if item in ingredients}

    products = set(df_recipes[[f"product_{k}" for k in range(1, 3)]].values.flatten()) - set([np.nan, None])
    items_uncraftable = (ingredients - products) - (set(raw_materials_1) | set(raw_materials_2))

    def ingredients_available(recipe_row):
        ingredients = recipe_row[[f"ingredient_{k}" for k in range(1, 5)]].values
        ingredients = [ing for ing in ingredients if pd.notnull(ing)]
        return all(ing not in items_uncraftable for ing in ingredients)

    df_recipes = df_recipes[df_recipes.apply(ingredients_available, axis=1)].copy()

    return raw_materials_1, raw_materials_limit_1, raw_materials_2, raw_materials_limit_2, df_recipes, items_uncraftable
