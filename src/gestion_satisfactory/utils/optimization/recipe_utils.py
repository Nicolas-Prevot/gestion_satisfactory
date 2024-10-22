import pandas as pd
import re


def extract_tier(unlocked_by):
    if pd.isnull(unlocked_by) or unlocked_by == '':
        return 0  # Default tier 0 for items without 'unlocked_by'
    match = re.search(r'Tier (\d+)', unlocked_by)
    if match:
        return int(match.group(1))
    else:
        return 0


def remove_uncraftable_rows(df_recipes, raw_materials_1_, raw_materials_2_, raw_materials_limit_1_, raw_materials_limit_2_):
    ingredients = set(df_recipes[[f'ingredient_{k}' for k in range(1,5)]].values.flatten()) - set([np.nan, None])

    raw_materials_1 = {item: value for item, value in raw_materials_1_.items() if item in ingredients}
    raw_materials_limit_1 = {item: value for item, value in raw_materials_limit_1_.items() if item in ingredients}
    raw_materials_2 = {item: value for item, value in raw_materials_2_.items() if item in ingredients}
    raw_materials_limit_2 = {item: value for item, value in raw_materials_limit_2_.items() if item in ingredients}

    products = set(df_recipes[[f'product_{k}' for k in range(1,3)]].values.flatten()) - set([np.nan, None])
    items_uncraftable = (ingredients - products) - (set(raw_materials_1) | set(raw_materials_2))

    def ingredients_available(recipe_row):
        ingredients = recipe_row[[f'ingredient_{k}' for k in range(1, 5)]].values
        ingredients = [ing for ing in ingredients if pd.notnull(ing)]
        return all(ing not in items_uncraftable for ing in ingredients)
    
    df_recipes = df_recipes[df_recipes.apply(ingredients_available, axis=1)].copy()

    return raw_materials_1, raw_materials_limit_1, raw_materials_2, raw_materials_limit_2, df_recipes, items_uncraftable