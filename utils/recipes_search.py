import pandas as pd


def get_recipes(item_name, df_recipes, rate_expected=None, normalized=True):
    rows_1 = df_recipes[df_recipes["item_out_1"] == item_name]
    rows_2 = df_recipes[df_recipes["item_out_2"] == item_name]
    rows = pd.concat([rows_1, rows_2])

    item_rate = []
    for index, row in rows.iterrows():
        if row["item_out_2"] == item_name:
            rate_base = row["rate_out_2"]
        else:
            rate_base = row["rate_out_1"]

        if normalized:
            rate=1
        elif rate_expected is not None:
            rate=rate_expected
        else:
            rate=rate_base

        rows.loc[index,"rate_out_1"] /= rate
        rows.loc[index,"rate_out_2"] /= rate
        rows.loc[index,"rate_in_1"] /= rate
        rows.loc[index,"rate_in_2"] /= rate
        rows.loc[index,"rate_in_3"] /= rate
        rows.loc[index,"rate_in_4"] /= rate
        item_rate.append(rate_base)
    rows["rate_base_item_selected"] = item_rate

    return rows


def extract_items(rows, items_to_avoid):
    items = list(rows["item_in_1"])+list(rows["item_in_2"])+list(rows["item_in_3"])+list(rows["item_in_4"])
    items = list(set(items))
    items = [e for e in items if e not in items_to_avoid and e is not None]
    return items


def get_rec_recipes(item_name, df_recipes, normalized=True):
    items_done = []
    recipes = {}
    items_todo = [item_name]
    while len(items_todo) != 0:
        item_todo = items_todo.pop()
        items_done.append(item_todo)
        rows = get_recipes(item_todo, df_recipes, normalized)
        recipes[item_todo] = rows
        if item_todo == "Water":
            continue
        items_todo += extract_items(rows, items_done)
    return recipes
