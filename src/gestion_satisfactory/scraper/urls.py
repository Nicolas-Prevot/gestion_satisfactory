from bs4 import BeautifulSoup
import requests
import pandas as pd
from typing import Tuple

from gestion_satisfactory.scraper.utils import (
    parse_building_description,
    parse_building_recipes,
    flatten_building_data,
    flatten_recipes,
    sttqdm,
    save_img,
)


def get_all_buildings_urls(url: str, streamlit_display: bool = False) -> pd.DataFrame:
    """
    Scrape all building URLs from the Satisfactory Wiki.

    Parameters
    ----------
    url : str
        The URL of the buildings page on the Satisfactory Wiki.
    streamlit_display : bool, optional
        Whether to display progress and messages using Streamlit, by default False.

    Returns
    -------
    pd.DataFrame
        DataFrame containing groups, subgroups, names, and URLs of buildings.

    """
    if streamlit_display:
        import streamlit as st

    data = []

    buildings_page = requests.get(url)
    buildings_soup = BeautifulSoup(buildings_page.content, "html.parser")

    navbox_tables = buildings_soup.find("tbody")

    for table in sttqdm(
        navbox_tables,
        total=len(navbox_tables),
        title="Scrapping the URLs of each building",
        streamlit_display=streamlit_display,
    ):
        th = table.find("th", scope="row")
        if not th:
            continue
        group_name = th.get_text(strip=True)

        sub_tables = table.find("tbody")
        if sub_tables:
            for sub_table in sub_tables:
                th = sub_table.find("th", scope="row")
                if not th:
                    continue
                sub_group_name = th.get_text(strip=True)
                links = sub_table.find_all("a")
                for a in links:
                    data.append(
                        {
                            "group": group_name,
                            "subgroup": sub_group_name,
                            "name": a.get("title") if a.get("title") else a.get_text(strip=True),
                            "url": a.get("href"),
                        }
                    )
        else:
            # No sub-tables, add links directly under the group
            links = table.find_all("a")
            for a in links:
                data.append(
                    {
                        "group": group_name,
                        "subgroup": None,  # No subgroup in this case
                        "name": a.get("title") if a.get("title") else a.get_text(strip=True),
                        "url": a.get("href"),
                    }
                )
    df = pd.DataFrame(data, columns=["group", "subgroup", "name", "url"])
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)

    if streamlit_display:
        st.success(f"{len(df)} buildings successfully found")

    return df


def get_all_dfs_production(
    base_url: str, df_production_buildings: pd.DataFrame, streamlit_display: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Scrape building information, recipes, and items for production buildings.

    Parameters
    ----------
    base_url : str
        The base URL of the Satisfactory Wiki.
    df_production_buildings : pd.DataFrame
        DataFrame containing URLs of production buildings.
    streamlit_display : bool, optional
        Whether to display progress and messages using Streamlit, by default False.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        A tuple containing DataFrames for buildings, recipes, and items.

    """
    if streamlit_display:
        import streamlit as st

    info_buildings = {}
    recipes_data = {}

    for row in df_production_buildings.itertuples():
        building_page = requests.get(base_url + row.url)
        building_soup = BeautifulSoup(building_page.content, "html.parser")

        building_description = building_soup.find("aside")
        info_building = parse_building_description(building_description)
        info_buildings[row.name] = info_building

        building_recipes = building_soup.find("table", class_="recipetable")
        info_buidling_recipes = parse_building_recipes(building_recipes)
        recipes_data[row.name] = info_buidling_recipes

        if streamlit_display:
            st.success(f"Informations on '{row.name}' are correctly parsed")

    # Flatten the building data
    flattened_data = flatten_building_data(info_buildings)
    # Convert flattened data to DataFrame
    buildings_df_ = pd.DataFrame.from_dict(flattened_data, orient="index")
    buildings_df = df_production_buildings.merge(buildings_df_, on="name", how="left")

    # Flatten the recipes
    flattened_recipes, items_list = flatten_recipes(recipes_data)
    # Convert to DataFrame
    recipes_df = pd.DataFrame(flattened_recipes)
    items_df = pd.DataFrame(items_list)
    items_df.drop_duplicates(inplace=True)
    items_df.reset_index(drop=True, inplace=True)

    return buildings_df, recipes_df, items_df


def save_imgs(
    df: pd.DataFrame, col_url: str, path_imgs: str, title: str, streamlit_display: bool = False
) -> pd.DataFrame:
    """
    Save images of items or buildings to the specified path.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data for items or buildings.
    col_url : str
        The column containing the image URL.
    path_imgs : str
        The path where images should be saved.
    title : str
        The title for the scraping process (items or buildings).
    streamlit_display : bool, optional
        Flag to enable Streamlit display during the process, by default False.

    Returns
    -------
    pd.DataFrame
        DataFrame with updated paths to the saved images.

    """
    if streamlit_display:
        import streamlit as st

    df["path_img"] = None
    for i, (name, url) in sttqdm(
        enumerate(zip(df.name, df[col_url])),
        title=f"Downloading {title} images",
        total=len(df.name),
        streamlit_display=streamlit_display,
    ):
        if not pd.isna(url):
            path_img = save_img(name, "https://satisfactory.wiki.gg" + url, path_imgs)
            df.path_img[i] = path_img
    if streamlit_display:
        st.success("Downloaded images and saved the paths successfully !")

    return df
