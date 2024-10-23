import streamlit as st
from streamlit_agraph import agraph

import pandas as pd
import numpy as np
import re
from typing import Tuple

from gestion_satisfactory.utils.optimization.optimize import get_optimize_prod
from gestion_satisfactory.utils.database.load_df import get_df_from_tables
from gestion_satisfactory.utils.display.grids import item_selector
from gestion_satisfactory.utils.display.graph import create_genealogy_graph
from gestion_satisfactory.utils.display.display import display_recipes_frame, display_items_balance
from gestion_satisfactory.utils.database.update_bdd_from_web import update_bdd
from gestion_satisfactory.utils.config.config import (
    raw_materials_1_,
    raw_materials_2_,
    raw_materials_limit_1_,
    raw_materials_limit_2_,
)
from gestion_satisfactory.utils.optimization.recipe_utils import extract_tier, remove_uncraftable_rows


@st.cache_data
def cached_get_df_from_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Cache and retrieve dataframes from tables.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        A tuple containing dataframes for items, buildings, and recipes.

    """
    return get_df_from_tables()


def create_page(title: str) -> None:
    """
    Create a Streamlit page for optimizing production recipes.

    Parameters
    ----------
    title : str
        The title of the page.

    Returns
    -------
    None

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

    df_recipes_["tier"] = df_recipes_["unlocked_by"].apply(extract_tier)
    df_buildings["tier"] = df_buildings["unlocked_by"].apply(extract_tier)

    product_columns = [f"product_{i}" for i in range(1, 3)]
    condition = ~(
        (df_recipes_["building_name"] == "Packager") & (df_recipes_[product_columns].eq("Empty Canister").any(axis=1))
    )
    df_recipes_ = df_recipes_[condition]

    max_tier = st.selectbox(
        label="Select the maximum technology tier to include:", options=[f"Tier {i}" for i in range(10)], index=9
    )
    max_tier_num = int(re.search(r"\d+", max_tier).group())

    df_recipes = df_recipes_[df_recipes_["tier"] <= max_tier_num].copy()

    buildings_unreachable = list(df_buildings[df_buildings["tier"] > max_tier_num]["name"])

    df_recipes = df_recipes[~df_recipes["building_name"].isin(buildings_unreachable)]

    # Remove uncraftable recipes
    raw_materials_1, raw_materials_limit_1, raw_materials_2, raw_materials_limit_2, df_recipes, items_uncraftable = (
        remove_uncraftable_rows(
            df_recipes, raw_materials_1_, raw_materials_2_, raw_materials_limit_1_, raw_materials_limit_2_
        )
    )
    while len(items_uncraftable) > 0:
        (
            raw_materials_1,
            raw_materials_limit_1,
            raw_materials_2,
            raw_materials_limit_2,
            df_recipes,
            items_uncraftable,
        ) = remove_uncraftable_rows(
            df_recipes, raw_materials_1, raw_materials_2, raw_materials_limit_1, raw_materials_limit_2
        )

    with st.expander(label="Change importance / weight on raw items"):
        col1, col2 = st.columns(spec=2)
        with col1:
            for i, item in enumerate(raw_materials_1):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body=f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_1[item] = st.slider(
                        label="t",
                        key=f"input1_{i}",
                        min_value=0.0,
                        max_value=50.0,
                        value=float(raw_materials_1[item]),
                        label_visibility="collapsed",
                    )
        with col2:
            for i, item in enumerate(raw_materials_2):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body=f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_2[item] = st.slider(
                        label="t",
                        key=f"input2_{i}",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(raw_materials_2[item]),
                        label_visibility="collapsed",
                    )

    with st.expander(label="Change limit on raw items"):
        col1, col2 = st.columns(spec=2)
        with col1:
            for i, item in enumerate(raw_materials_limit_1):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body=f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_limit_1[item] = st.slider(
                        label="t",
                        key=f"input_limit_1_{i}",
                        min_value=0,
                        step=1,
                        max_value=10000,
                        value=int(raw_materials_limit_1[item]),
                        label_visibility="collapsed",
                    )
        with col2:
            for i, item in enumerate(raw_materials_limit_2):
                col1_1, col1_2 = st.columns(spec=2)
                with col1_1:
                    src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                    st.markdown(body=f'<img src="{src_img}" width=40px>   {item}', unsafe_allow_html=True)
                with col1_2:
                    raw_materials_limit_2[item] = st.slider(
                        label="t",
                        key=f"input_limit_2_{i}",
                        min_value=0,
                        step=1,
                        max_value=1000,
                        value=int(raw_materials_limit_2[item]),
                        label_visibility="collapsed",
                    )

    raw_items = list(raw_materials_1) + list(raw_materials_2)
    not_raw_items = (
        set(df_recipes[[f"ingredient_{k}" for k in range(1, 5)]].values.flatten())
        | set(df_recipes[[f"product_{k}" for k in range(1, 3)]].values.flatten())
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
                quantities.append(st.slider(label=f"Desired number of {e.name} :", min_value=0, step=1, value=30))

    weights_raw_items_dict = raw_materials_1 | {key: value * 1000 for key, value in raw_materials_2.items()}
    limits_raw_items_dict = raw_materials_limit_1 | raw_materials_limit_2
    selected_products = dict(zip(items_to_produce, quantities))

    if item_to_optim_prod["selected_rows"] is not None:
        recipe_vars, recipe_var_to_name, status = get_optimize_prod(
            df_recipes, raw_items, weights_raw_items_dict, limits_raw_items_dict, not_raw_items, selected_products
        )

        if status == "Optimal":
            st.success(body="Optimal solution found!")
        elif status == "Infeasible":
            st.warning(
                body="Request Infeasible. Try reducing the expected amount of outputs or increase the limits on raw ressources"
            )
        else:
            st.error(body=f"Issue during optimization : '{status}'")

        tab1, tab2, tab3 = st.tabs(tabs=["Recipes", "Materials", "Graph"])

        with tab1:
            display_recipes_frame(df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name, 1e-4)

        with tab2:
            display_items_balance(
                df_recipes, df_items, df_buildings, raw_items, not_raw_items, recipe_vars, recipe_var_to_name, 1e-4
            )

        with tab3:
            nodes, edges, config = create_genealogy_graph(
                df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name, 1e-4
            )
            return_value = agraph(nodes=nodes, edges=edges, config=config)
