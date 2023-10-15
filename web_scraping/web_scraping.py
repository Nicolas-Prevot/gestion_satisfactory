from omegaconf import OmegaConf
from pathlib import Path

from web_scraping.urls import get_all_item_URLs
from web_scraping.utils import get_all_dfs


def get_configurable_parameters(config_path: str):
    config = OmegaConf.load(config_path)
    path_imgs = Path(config.project.path_imgs)
    path_imgs.mkdir(parents=True, exist_ok=True)
    return config


def create_dfs(streamlit_display=False):
    config = get_configurable_parameters("web_scraping/config_scraping.yaml")

    all_item_URLs = get_all_item_URLs()
    print(all_item_URLs)
    print(len(all_item_URLs))

    df_items, df_buildings, df_recipes = get_all_dfs(all_item_URLs, config, streamlit_display)

    return df_items, df_buildings, df_recipes


if __name__ == '__main__':
    create_dfs()