from web_scraping.urls import get_all_buildings_urls, get_all_dfs_production, save_imgs

def create_dfs(streamlit_display=False):
    path_imgs = "static/"

    df_buildings_urls = get_all_buildings_urls("https://satisfactory.wiki.gg/wiki/Buildings", streamlit_display)
    production_buildings = df_buildings_urls[df_buildings_urls["subgroup"].isin(["Smelters", "Manufacturers"])]

    buildings_df, recipes_df, items_df = get_all_dfs_production("https://satisfactory.wiki.gg", production_buildings, streamlit_display)
    buildings_df = df_buildings_urls.merge(buildings_df, on=['group', 'subgroup', 'name', 'url'], how='left')

    items_df = save_imgs(items_df, "url", path_imgs, "items", streamlit_display)
    buildings_df = save_imgs(buildings_df, "image_path", path_imgs, "buildings", streamlit_display)

    return buildings_df, recipes_df, items_df


if __name__ == '__main__':
    create_dfs()