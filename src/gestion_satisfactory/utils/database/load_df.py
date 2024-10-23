import base64
import pandas as pd
from typing import Tuple, List, Optional

from gestion_satisfactory.utils.database.connect_bdd import load_df


def ReadPictureFile(wch_fl: str) -> str:
    """
    Read an image file and return its base64 encoded string.

    Parameters
    ----------
    wch_fl : str
        The file path of the image to read.

    Returns
    -------
    str
        Base64 encoded string of the image, or an empty string if an error occurs.

    """
    try:
        return base64.b64encode(open(wch_fl, "rb").read()).decode()

    except Exception:
        return ""


def get_df_from_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and process DataFrames for items, buildings, and recipes from the database.

    This function loads the 'items', 'buildings', and 'recipes' tables from the database.
    It also processes image paths and encodes images in base64 for web display.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        A tuple containing DataFrames for items, buildings, and recipes respectively.

    """
    df_items = load_df("items")
    new_path: List[Optional[str]] = []
    new_path_web: List[Optional[str]] = []
    for i, url in enumerate(df_items["path_img"]):
        new_path.append("app/" + url)
        imgExtn = url[-4:]
        new_path_web.append(f"data:image/{imgExtn};base64," + ReadPictureFile(url))
    df_items["streamlit_path_img"] = new_path
    df_items["web_img"] = new_path_web

    df_buildings = load_df("buildings")
    new_path = []
    new_path_web = []
    for i, url in enumerate(df_buildings["path_img"]):
        if pd.isna(url):
            new_path.append(None)
            new_path_web.append(None)
        else:
            new_path.append("app/" + url)
            imgExtn = url[-4:]
            new_path_web.append(f"data:image/{imgExtn};base64," + ReadPictureFile(url))
    df_buildings["streamlit_path_img"] = new_path
    df_buildings["web_img"] = new_path_web

    df_recipes = load_df("recipes")

    return df_items, df_buildings, df_recipes
