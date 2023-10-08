from streamlit_agraph import agraph, Node, Edge, Config
import numpy as np
import streamlit as st

from utils.recipes_search import extract_items


def create_genealogy_graph(recipes, item_to_img, blacklist):
    items = [*recipes]
    nodes = []
    edges = []

    for item in items:
        #if item not in blacklist:
        nodes.append(Node(id=item,
                        label=item,
                        size=15,
                        image=item_to_img[item],
                        shape="circularImage"))
    
    for item in items:
        if item not in blacklist:
            rows = recipes[item]
            items_for_item = extract_items(rows, [])
            for item2 in items_for_item:
                if item2 in items:# and item2 not in blacklist:
                    edges.append(Edge(source=item2, target=item))


    config = Config(width=750,
                    height=950,
                    directed=True, 
                    physics=True, 
                    hierarchical=False
                    )

    return nodes, edges, config


def create_recipe_optimize(df_items, df_buildings, df_recipes, recipe_names, Lmbda_soln):
    config = Config(width=750,
                    height=650,
                    directed=True,
                    physics=True,
                    hierarchical=False
                    )
    THRESHOLD = 1e-10
    nodes = []
    edges = []
    items = []

    for id_recipe_used in np.where(Lmbda_soln > THRESHOLD)[0]:
        recipe = df_recipes[df_recipes["name"] == recipe_names[id_recipe_used]]
        name_building = recipe["building"].tolist()[0]
        image_building = df_buildings[df_buildings["name"] == name_building]["web_img"].tolist()[0]
        nodes.append(Node(id=recipe_names[id_recipe_used],
                          label=recipe_names[id_recipe_used],
                          size=22,
                          image=image_building,
                          shape="circularImage"))
        
        for i in range(1,3):
            if recipe[f"item_out_{i}"].tolist()[0] is not None:
                items.append(recipe[f"item_out_{i}"].tolist()[0])
        for i in range(1,5):
            if recipe[f"item_in_{i}"].tolist()[0] is not None:
                items.append(recipe[f"item_in_{i}"].tolist()[0])

    items = list(set(items))
    for item in items:
        nodes.append(Node(id=f"{item}_item",
                          label=item,
                          size=11,
                          image=df_items[df_items["name"] == item]["web_img"].tolist()[0],
                          shape="circularImage"))
    
    for id_recipe_used in np.where(Lmbda_soln > THRESHOLD)[0]:
        recipe = df_recipes[df_recipes["name"] == recipe_names[id_recipe_used]]

        for i in range(1,3):
            item_out = recipe[f"item_out_{i}"].tolist()[0]
            if item_out is not None:
                edges.append(Edge(source=recipe_names[id_recipe_used], target=f"{item_out}_item"))

        for i in range(1,5):
            item_in = recipe[f"item_in_{i}"].tolist()[0]
            if item_in is not None:
                edges.append(Edge(source=f"{item_in}_item", target=recipe_names[id_recipe_used]))

    
    return nodes, edges, config
