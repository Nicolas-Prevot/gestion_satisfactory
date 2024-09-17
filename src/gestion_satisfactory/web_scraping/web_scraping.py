from web_scraping.urls import get_all_item_URLs
from web_scraping.utils import get_all_dfs


def create_dfs(streamlit_display=False):
    path_imgs = "static/"

    all_item_URLs = get_all_item_URLs()
    df_items, df_buildings, df_recipes = get_all_dfs(all_item_URLs, path_imgs, streamlit_display)

    return df_items, df_buildings, df_recipes


if __name__ == '__main__':
    create_dfs()