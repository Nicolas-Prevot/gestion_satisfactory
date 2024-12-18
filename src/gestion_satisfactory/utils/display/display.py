from typing import Optional, Dict, Any, List, Union, Mapping
import pandas as pd
import math
import streamlit as st

MD_LEFT_ALIGNED = ":-"
MD_CENTER_ALIGNED = ":-:"
MD_RIGHT_ALIGNED = "-:"
OC_COLOR = "#FF7700"
NB_BUILDING_COLOR = "#00A9FF"
RATE_COLOR = "#00C800"


def get_item_display(img: str, name: Optional[str], rate: float = 0, oc: float = 0, nb_building: float = 0) -> str:
    """
    Generate HTML content to display an item with its details.

    Parameters
    ----------
    img : str
        URL or path to the item's image.
    name : str or None
        Name of the item.
    rate : float, optional
        Production rate of the item, by default 0.
    oc : float, optional
        Overclock factor, by default 0.
    nb_building : float, optional
        Number of buildings producing the item, by default 0.

    Returns
    -------
    str
        HTML string representing the item's display content.

    """
    string = ""
    if name is None:
        return string
    final_rate = rate * oc * nb_building
    if rate != 0:
        string = f'<figure class="image" style="margin: 0px;"><img src="{img}" width=50px>\
                    <figcaption style="font-size: 12px;">\
                        {rate}\
                        x\
                        <span style="color:{NB_BUILDING_COLOR}">{nb_building:.2f}</span>\
                        x\
                        <span style="color:{OC_COLOR}">{oc:.2f}</span> =\
                        <br/><span style="color:{RATE_COLOR}">{final_rate:.2f}</span>\
                        <br/>{name.replace("_", " ")}\
                    </figcaption>\
                </figure>'
    else:
        string = f'<figure class="image" style="margin: 0px;"><img src="{img}" width=75px>\
                    <figcaption style="font-size: 12px;">\
                        {name}\
                    </figcaption>\
                 </figure>'
    return string


def get_row_text(infos: Dict[str, Any]) -> str:
    """
    Construct a markdown table row with recipe information.

    Parameters
    ----------
    infos : dict
        Dictionary containing recipe and item information.

    Returns
    -------
    str
        A markdown-formatted string representing a table row.

    """
    return f'|{infos["recipe_name"]}\
        |{"🔄" if infos["alternative"] else "🟦"}\
        |{get_item_display(infos["img_product_1"], infos["name_product_1"], infos["rate_product_1"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_product_2"], infos["name_product_2"], infos["rate_product_2"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_building"], infos["name_building"])}\
        |{get_item_display(infos["img_ingredient_1"], infos["name_ingredient_1"], infos["rate_ingredient_1"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_2"], infos["name_ingredient_2"], infos["rate_ingredient_2"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_3"], infos["name_ingredient_3"], infos["rate_ingredient_3"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_4"], infos["name_ingredient_4"], infos["rate_ingredient_4"], infos["overclock"], infos["nb_building"])}\
        |{infos["overclock"]}\
        |{infos["nb_building"]:.2f}|\n'


def display_recipes_frame(
    df_recipes: pd.DataFrame,
    df_items: pd.DataFrame,
    df_buildings: pd.DataFrame,
    recipe_vars: Dict[str, float],
    recipe_var_to_name: Dict[str, str],
    THRESHOLD: float = 1e-4,
) -> None:
    """
    Display a markdown table of recipes based on provided variables.

    Parameters
    ----------
    df_recipes : pd.DataFrame
        DataFrame containing recipes.
    df_items : pd.DataFrame
        DataFrame containing items.
    df_buildings : pd.DataFrame
        DataFrame containing buildings.
    recipe_vars : dict
        Dictionary mapping recipe variable names to their amounts.
    recipe_var_to_name : dict
        Dictionary mapping recipe variable names to recipe names.
    threshold : float, optional
        Threshold below which values are considered negligible, by default 1e-4.

    Returns
    -------
    None

    """
    title_line = f'|Recipe name|Alt.|Out 1|Out 2|Buidling|In 1|In 2|In 3|In 4|<span style="color:{OC_COLOR}">OC</span>|<span style="color:{NB_BUILDING_COLOR}">Nb Building</span>|'
    setup_line = f"|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_CENTER_ALIGNED}|"

    markdown_text = title_line + "\n" + setup_line + "\n"

    for var_name, amount in recipe_vars.items():
        if amount < THRESHOLD:
            continue
        recipe_name = recipe_var_to_name[var_name]
        infos_row = {"recipe_name": recipe_name, "nb_building": amount, "overclock": 1}

        row = df_recipes[df_recipes["recipe_name"] == recipe_name]
        duration = row["duration"].values[0]
        if len(row) != 0:
            iter_items = {"product": 2, "ingredient": 4}
            for inout in iter_items:
                for i in range(1, iter_items[inout] + 1):
                    item = row[f"{inout}_{i}"].values[0]
                    if item is None:
                        src_img = None
                        rate = None
                    else:
                        src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                        rate = 60 * row[f"{inout}_amount_{i}"].values[0] / duration
                    infos_row[f"img_{inout}_{i}"] = src_img
                    infos_row[f"name_{inout}_{i}"] = item
                    infos_row[f"rate_{inout}_{i}"] = rate

            name_building = row["building_name"].values[0]
            img_building = df_buildings[df_buildings["name"] == name_building]["web_img"].tolist()[0]
            infos_row["name_building"] = name_building
            infos_row["img_building"] = img_building
            infos_row["alternative"] = row["recipe_alternate"].values[0]

            markdown_text += get_row_text(infos_row)

    st.markdown(body=markdown_text, unsafe_allow_html=True)


def display_items_in_columns(df_items: pd.DataFrame, items_dict: Mapping[str, Union[int, float]], title: str) -> None:
    """
    Display items in columns with their corresponding values.

    Parameters
    ----------
    df_items : pd.DataFrame
        DataFrame containing item information.
    items_dict : dict
        Dictionary of items and their values to display.
    title : str
        Title for the section.

    Returns
    -------
    None

    """
    st.write(f"### {title}")
    if items_dict:
        items = list(items_dict.items())
        num_cols = 3
        cols = st.columns(spec=num_cols)
        for idx, (item, value) in enumerate(items):
            col = cols[idx % num_cols]
            src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
            with col:
                markdown_text = (
                    f'<div style="text-align: center;"><img src="{src_img}" width="40px"><br>{item}: {value:.2f}</div>'
                )
                st.markdown(body=markdown_text, unsafe_allow_html=True)
    else:
        st.write(f"No {title.lower()} to display.")


def display_buildings_in_columns(df_buildings: pd.DataFrame, building_counts: Dict[str, int], title: str) -> None:
    """
    Display building counts in columns.

    Parameters
    ----------
    df_buildings : pd.DataFrame
        DataFrame containing building information.
    building_counts : dict
        Dictionary of building names and their counts.
    title : str
        Title for the section.

    Returns
    -------
    None

    """
    st.write(f"### {title}")
    st.info(
        body="Note: The number of buildings required is calculated by rounding up the required amount for each recipe individually and summing them up. This ensures that each recipe has the necessary full buildings allocated."
    )
    if building_counts:
        buildings = list(building_counts.items())
        num_cols = 3
        cols = st.columns(spec=num_cols)
        for idx, (building, count) in enumerate(buildings):
            col = cols[idx % num_cols]
            src_img = df_buildings[df_buildings["name"] == building]["web_img"].tolist()[0]
            with col:
                markdown_text = (
                    f'<div style="text-align: center;"><img src="{src_img}" width="40px"><br>{building}: {count}</div>'
                )
                st.markdown(body=markdown_text, unsafe_allow_html=True)
    else:
        st.write(f"No {title.lower()} to display.")


def display_items_balance(
    df_recipes: pd.DataFrame,
    df_items: pd.DataFrame,
    df_buildings: pd.DataFrame,
    raw_items: List[str],
    not_raw_items: List[str],
    recipe_vars: Dict[str, float],
    recipe_var_to_name: Dict[str, str],
    THRESHOLD: float = 1e-4,
) -> None:
    """
    Display the balance of items and buildings based on recipe variables.

    Parameters
    ----------
    df_recipes : pd.DataFrame
        DataFrame containing recipes.
    df_items : pd.DataFrame
        DataFrame containing items.
    df_buildings : pd.DataFrame
        DataFrame containing buildings.
    raw_items : list
        List of raw item names.
    not_raw_items : list
        List of non-raw item names.
    recipe_vars : dict
        Dictionary mapping recipe variable names to their amounts.
    recipe_var_to_name : dict
        Dictionary mapping recipe variable names to recipe names.
    threshold : float, optional
        Threshold below which values are considered negligible, by default 1e-4.

    Returns
    -------
    None

    """
    all_items = raw_items + not_raw_items
    items_output = dict.fromkeys(all_items, 0)
    building_counts = {}

    for var_name, amount in recipe_vars.items():
        if amount < THRESHOLD:
            continue

        recipe_name = recipe_var_to_name[var_name]
        idx = df_recipes[df_recipes["recipe_name"] == recipe_name].index[0]
        duration = df_recipes.at[idx, "duration"]

        building_name = df_recipes.at[idx, "building_name"]
        if building_name not in building_counts:
            building_counts[building_name] = 0
        building_counts[building_name] += math.ceil(amount)

        for item in all_items:
            net_prod = sum(
                df_recipes.at[idx, f"product_amount_{product_idx}"]
                for product_idx in range(1, 3)
                if df_recipes.at[idx, f"product_{product_idx}"] == item
            ) - sum(
                df_recipes.at[idx, f"ingredient_amount_{ingredient_idx}"]
                for ingredient_idx in range(1, 5)
                if df_recipes.at[idx, f"ingredient_{ingredient_idx}"] == item
            )
            net_prod_per_minute = net_prod * 60 * amount / duration
            items_output[item] += net_prod_per_minute

    items_output = {item: value for item, value in items_output.items() if abs(value) > THRESHOLD}

    raw_items_output = {item: value for item, value in items_output.items() if item in raw_items}
    not_raw_items_output = {item: value for item, value in items_output.items() if item in not_raw_items}

    display_items_in_columns(df_items, raw_items_output, "Consumption of raw ressources")
    st.divider()
    display_items_in_columns(df_items, not_raw_items_output, "Items production")
    st.divider()
    display_buildings_in_columns(df_buildings, building_counts, "Buildings Needed")


def display_results_item(
    df_factory_planner: pd.DataFrame, df_items: pd.DataFrame, display_in_expander: bool = False
) -> None:
    """
    Display the results of item production and consumption.

    Parameters
    ----------
    df_factory_planner : pd.DataFrame
        DataFrame containing factory planning information.
    df_items : pd.DataFrame
        DataFrame containing item information.
    display_in_expander : bool, optional
        If True, display the results within an expander widget; otherwise, display directly.
        Default is False.

    Returns
    -------
    None

    """
    results_production: Dict[str, float] = {}
    results_consommation: Dict[str, float] = {}
    power_usage: float = 0.0
    for i, row in df_factory_planner.iterrows():
        for k in range(2):
            if row[f"product_{k+1}"] is not None:
                if row[f"product_{k+1}"] not in list(results_production.keys()):
                    results_production[row[f"product_{k+1}"]] = 0
                results_production[row[f"product_{k+1}"]] += (
                    (60 * float(row[f"product_amount_{k+1}"]) / float(row["duration"]))
                    * float(row["nb_building"])
                    * float(row["rate/overclock"])
                )

        for k in range(4):
            if row[f"ingredient_{k+1}"] is not None:
                if row[f"ingredient_{k+1}"] not in list(results_consommation.keys()):
                    results_consommation[row[f"ingredient_{k+1}"]] = 0
                results_consommation[row[f"ingredient_{k+1}"]] -= (
                    (60 * float(row[f"ingredient_amount_{k+1}"]) / float(row["duration"]))
                    * float(row["nb_building"])
                    * float(row["rate/overclock"])
                )

        if row["power_usage"] is not None:
            power_usage += float(row["power_usage"]) * float(row["nb_building"]) * float(row["rate/overclock"])
        elif (row["min_consumption"] is not None) and (row["max_consumption"] is not None):
            power_usage += (
                (float(row["max_consumption"]) - float(row["min_consumption"]))
                * float(row["nb_building"])
                * float(row["rate/overclock"])
                / 2
            )

    results_positive = {}
    results_negative = {}
    results_negative_imports = {}
    for item in results_consommation:
        if item in list(results_production.keys()):
            result = results_consommation[item] + results_production[item]
            if result < 0:
                results_negative[item] = result
            else:
                results_positive[item] = result
        else:
            results_negative_imports[item] = results_consommation[item]

    for item in results_production:
        if item not in list(results_consommation.keys()):
            results_positive[item] = results_production[item]

    st.write(f"⚡ {power_usage} MW ⚡")

    def write_cols():
        col1, col2, col3 = st.columns(spec=3)
        with col1:
            if len(results_positive) != 0:
                for item in results_positive:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    markdown_text = f'<img src="{df_items[df_items["name"] == item]["web_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                    **<span style="color:#63ACFF">{results_positive[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)'
                    st.markdown(body=markdown_text, unsafe_allow_html=True)
        with col2:
            if len(results_negative) != 0:
                for item in results_negative:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    markdown_text = f'<img src="{df_items[df_items["name"] == item]["web_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                    **<span style="color:#FF5154">{results_negative[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)'
                    st.markdown(body=markdown_text, unsafe_allow_html=True)
        with col3:
            if len(results_negative_imports) != 0:
                for item in results_negative_imports:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    markdown_text = f'<img src="{df_items[df_items["name"] == item]["web_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                    **<span style="color:#FF5154">{results_negative_imports[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)'
                    st.markdown(body=markdown_text, unsafe_allow_html=True)

    if display_in_expander:
        with st.expander(label="Results"):
            write_cols()
    else:
        write_cols()
