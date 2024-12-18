from streamlit_agraph import Node, Edge, Config
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd


def create_genealogy_graph(
    df_recipes: pd.DataFrame,
    df_items: pd.DataFrame,
    df_buildings: pd.DataFrame,
    recipe_vars: Dict[str, float],
    recipe_var_to_name: Dict[str, str],
    THRESHOLD: float = 1e-4,
) -> Tuple[List[Node], List[Edge], Config]:
    """
    Create a genealogy graph representing the relationships between recipes and items.

    Parameters
    ----------
    df_recipes : pd.DataFrame
        DataFrame containing recipe information.
    df_items : pd.DataFrame
        DataFrame containing item information.
    df_buildings : pd.DataFrame
        DataFrame containing building information.
    recipe_vars : dict
        Dictionary mapping recipe variable names to their quantities.
    recipe_var_to_name : dict
        Dictionary mapping recipe variable names to recipe names.
    THRESHOLD : float, optional
        Threshold value below which a recipe amount is considered negligible, by default 1e-4.

    Returns
    -------
    Tuple[List[Node], List[Edge], Config]
        A tuple containing the list of nodes, list of edges, and graph configuration for visualization.

    """
    config = Config(width=9000, height=650, directed=True, physics=True, hierarchical=False)
    nodes = []
    edges = []
    items = []

    for var_name, amount in recipe_vars.items():
        if amount < THRESHOLD:
            continue

        recipe_name = recipe_var_to_name[var_name]
        recipe = df_recipes[df_recipes["recipe_name"] == recipe_name]
        name_building = recipe["building_name"].tolist()[0]
        image_building = df_buildings[df_buildings["name"] == name_building]["web_img"].tolist()[0]

        nodes.append(Node(id=recipe_name, label=recipe_name, size=40, image=image_building, shape="circularImage"))

        items += list(
            (
                set(recipe[[f"ingredient_{k}" for k in range(1, 5)]].values.flatten())
                | set(recipe[[f"product_{k}" for k in range(1, 3)]].values.flatten())
            )
            - set([np.nan, None])
        )

    items = list(set(items))
    for item in items:
        nodes.append(
            Node(
                id=f"{item}_item",
                label=item,
                size=22,
                image=df_items[df_items["name"] == item]["web_img"].tolist()[0],
                shape="circularImage",
            )
        )

    for var_name, amount in recipe_vars.items():
        if amount < THRESHOLD:
            continue

        recipe_name = recipe_var_to_name[var_name]
        recipe = df_recipes[df_recipes["recipe_name"] == recipe_name]

        for i in range(1, 3):
            item_out = recipe[f"product_{i}"].tolist()[0]
            if item_out is not None:
                edges.append(Edge(source=recipe_name, target=f"{item_out}_item"))

        for i in range(1, 5):
            item_in = recipe[f"ingredient_{i}"].tolist()[0]
            if item_in is not None:
                edges.append(Edge(source=f"{item_in}_item", target=recipe_name))

    return nodes, edges, config
