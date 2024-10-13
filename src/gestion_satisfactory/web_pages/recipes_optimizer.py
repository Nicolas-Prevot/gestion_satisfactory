import streamlit as st
from streamlit_agraph import agraph

import os
import pandas as pd
import numpy as np
from PIL import Image
import re

from gestion_satisfactory.utils.optimize import get_optimize_prod
from gestion_satisfactory.utils.load_df import get_df_from_tables
from gestion_satisfactory.utils.grids import item_selector
from gestion_satisfactory.utils.graph import create_genealogy_graph
from gestion_satisfactory.utils.display import display_recipes_frame, display_items_balance
from gestion_satisfactory.utils.update_bdd_from_web import update_bdd

raw_materials_1_ = {
    'Limestone':1.,
    'Iron Ore':1.,
    'Copper Ore':1.,
    'Coal':2.,
    'Sulfur':2.,
    'Raw Quartz':4.,
    'Bauxite':8.,
    'Caterium Ore':6.,
    'Water':0.,
    'Crude Oil':.5,
    'Nitrogen Gas':6.,
    'Uranium':12.,
    'SAM':50.,
    'Uranium Waste':10.,
    'Plutonium Waste':10.,
}

raw_materials_2_ = {
    'Mycelia':1.,
    'Leaves':1.,
    'Wood':1.,
    'Blue Power Slug':1.,
    'Purple Power Slug':1.,
    'Yellow Power Slug':1.,
    'Stinger Remains':1.,
    'Hog Remains':1.,
    'Hatcher Remains':1.,
    'Spitter Remains':1.,
    'FICSMAS Tree Branch':1.,
    'FICSMAS Bow':1.,
    'Actual Snow':1.,
    'Candy Cane':1.,
}

raw_materials_limit_1_ = {
    'Limestone':5000.,
    'Iron Ore':5000.,
    'Copper Ore':5000.,
    'Coal':5000.,
    'Sulfur':5000.,
    'Raw Quartz':4000.,
    'Bauxite':2000.,
    'Caterium Ore':1000.,
    'Water':10000.,
    'Crude Oil':8000.,
    'Nitrogen Gas':1000.,
    'Uranium':1000.,
    'SAM':500.,
    'Uranium Waste':10.,
    'Plutonium Waste':10.,
}

raw_materials_limit_2_ = {
    'Mycelia':200.,
    'Leaves':200.,
    'Wood':200.,
    'Blue Power Slug':200.,
    'Purple Power Slug':200.,
    'Yellow Power Slug':200.,
    'Stinger Remains':200.,
    'Hog Remains':200.,
    'Hatcher Remains':200.,
    'Spitter Remains':200.,
    'FICSMAS Tree Branch':200.,
    'FICSMAS Bow':200.,
    'Actual Snow':200.,
    'Candy Cane':200.,
}

@st.cache_data
def cached_get_df_from_tables():
    return get_df_from_tables()


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


def create_page(title: str) -> None:
    """
    Create a streamlit page.

    Parameters
    ----------
    title: str, optional
        The title of the page.

    """
    title = "Optimize your production recipes"
    st.write(
        f"""<h1 style='text-align: center;'>
        ⚙️🏭 <i>{title}</i> 📈🔧
        </h1>""",
        unsafe_allow_html=True,
        )

    try:
        df_items, df_buildings, df_recipes_ = cached_get_df_from_tables()
    except:
        update_bdd(streamlit_display=True)
        st.rerun()

    df_recipes_['tier'] = df_recipes_['unlocked_by'].apply(extract_tier)
    df_buildings['tier'] = df_buildings['unlocked_by'].apply(extract_tier)

    product_columns = [f'product_{i}' for i in range(1, 3)]
    condition = ~(
        (df_recipes_['building_name'] == 'Packager') &
        (df_recipes_[product_columns].eq('Empty Canister').any(axis=1))
    )
    df_recipes_ = df_recipes_[condition]

    max_tier = st.selectbox(
        label = "Select the maximum technology tier to include:",
        options = [f"Tier {i}" for i in range(10)],
        index = 9,
    )
    max_tier_num = int(re.search(r'\d+', max_tier).group())

    df_recipes = df_recipes_[df_recipes_['tier'] <= max_tier_num].copy()

    buildings_unreachable = list(df_buildings[df_buildings['tier'] > max_tier_num]["name"])

    df_recipes = df_recipes[~df_recipes['building_name'].isin(buildings_unreachable)]

    # Remove uncraftable recipes
    raw_materials_1, raw_materials_limit_1, raw_materials_2, raw_materials_limit_2, df_recipes, items_uncraftable = remove_uncraftable_rows(df_recipes, raw_materials_1_, raw_materials_2_, raw_materials_limit_1_, raw_materials_limit_2_)
    while len(items_uncraftable) > 0:
        raw_materials_1, raw_materials_limit_1, raw_materials_2, raw_materials_limit_2, df_recipes, items_uncraftable = remove_uncraftable_rows(df_recipes, raw_materials_1, raw_materials_2, raw_materials_limit_1, raw_materials_limit_2)


    with st.expander(label = "Change importance / weight on raw items"):
        col1, col2 = st.columns(spec=2)
        with col1:
            for i, item in enumerate(raw_materials_1):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body = f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_1[item] = st.slider(label = "t", key=f"input1_{i}", min_value=0., max_value=50., value=float(raw_materials_1[item]), label_visibility= "collapsed")
        with col2:
            for i, item in enumerate(raw_materials_2):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body = f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_2[item] = st.slider(label = "t", key=f"input2_{i}", min_value=0., max_value=100., value=float(raw_materials_2[item]), label_visibility= "collapsed")
    
    with st.expander(label = "Change limit on raw items"):
        col1, col2 = st.columns(spec=2)
        with col1:
            for i, item in enumerate(raw_materials_limit_1):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body = f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_limit_1[item] = st.slider(label = "t", key=f"input_limit_1_{i}", min_value=0, step=1, max_value=10000, value=int(raw_materials_limit_1[item]), label_visibility= "collapsed")
        with col2:
            for i, item in enumerate(raw_materials_limit_2):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body = f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_limit_2[item] = st.slider(label = "t", key=f"input_limit_2_{i}", min_value=0, step=1, max_value=1000, value=int(raw_materials_limit_2[item]), label_visibility= "collapsed")
    
    raw_items = list(raw_materials_1)+list(raw_materials_2)
    not_raw_items = (set(df_recipes[[f'ingredient_{k}' for k in range(1,5)]].values.flatten()) | 
                     set(df_recipes[[f'product_{k}' for k in range(1,3)]].values.flatten())
                    ) - set([np.nan, None])
    not_raw_items -= set(raw_items)
    not_raw_items = list(not_raw_items)

    with st.sidebar:
        df_not_raw_items = df_items[df_items["name"].isin(not_raw_items)]
        item_to_optim_prod = item_selector(df_not_raw_items)

        items_to_produce = []
        quantities = []
        if item_to_optim_prod["selected_rows"] is not None:
            for e in item_to_optim_prod["selected_rows"].itertuples():
                items_to_produce.append(e.name)
                quantities.append(st.slider(label = f"Desired number of {e.name} :", min_value=0, step=1, value=30))
        
    weights_raw_items_dict = raw_materials_1 | {key: value * 1000 for key, value in raw_materials_2.items()}
    limits_raw_items_dict = raw_materials_limit_1 | raw_materials_limit_2
    selected_products = dict(zip(items_to_produce, quantities))
    
    if item_to_optim_prod["selected_rows"] is not None:
        recipe_vars, recipe_var_to_name, status = get_optimize_prod(df_recipes, raw_items, weights_raw_items_dict, limits_raw_items_dict, not_raw_items, selected_products)

        if status == "Optimal":
            st.success(body = "Optimal solution found!")
        elif status == "Infeasible":
            st.warning(body = f"Request Infeasible. Try reducing the expected amount of outputs or increase the limits on raw ressources")
        else:
            st.error(body = f"Issue during optimization : '{status}'")

        tab1, tab2, tab3 = st.tabs(tabs = ["Recipes", "Materials", "Graph"])

        with tab1:
            display_recipes_frame(df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name, 1e-4)   
        
        with tab2:
            display_items_balance(df_recipes, df_items, df_buildings, raw_items, not_raw_items, recipe_vars, recipe_var_to_name, 1e-4)

        with tab3:
            nodes, edges, config = create_genealogy_graph(df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name, 1e-4)
            return_value = agraph(nodes=nodes, edges=edges, config=config)
