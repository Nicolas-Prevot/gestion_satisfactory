import base64
import pandas as pd

from utils.connect_bdd import load_df


def ReadPictureFile(wch_fl):
    try:
        return base64.b64encode(open(wch_fl, 'rb').read()).decode()

    except:
        return ""


def get_df_from_tables():

    df_items = load_df("items")
    new_path = []
    new_path_web = []
    for i,url in enumerate(df_items["path_img"]):
        new_path.append("app/"+url)
        imgExtn = url[-4:]
        new_path_web.append(f'data:image/{imgExtn};base64,' + ReadPictureFile(url))
    df_items["streamlit_path_img"] = new_path
    df_items["web_img"] = new_path_web

    df_buildings = load_df("buildings")
    new_path = []
    new_path_web = []
    for i,url in enumerate(df_buildings["path_img"]):
        if pd.isna(url):
            new_path.append(None)
            new_path_web.append(None)
        else:
            new_path.append("app/"+url)
            imgExtn = url[-4:]
            new_path_web.append(f'data:image/{imgExtn};base64,' + ReadPictureFile(url))
    df_buildings["streamlit_path_img"] = new_path
    df_buildings["web_img"] = new_path_web

    df_recipes = load_df("recipes")
    
    return df_items, df_buildings, df_recipes