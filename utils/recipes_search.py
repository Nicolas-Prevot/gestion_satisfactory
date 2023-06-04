import pandas as pd


def get_recipes(item_name, df_recipes):
    rows_1 = df_recipes[df_recipes["item_out_1"] == item_name]
    rows_2 = df_recipes[df_recipes["item_out_2"] == item_name]
    rows = pd.concat([rows_1, rows_2])
    return rows


def get_rec_recipes(item_name, df_recipes):
    pass
