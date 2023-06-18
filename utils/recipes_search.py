import pandas as pd
import numpy as np
import copy


def get_recipes(item_name, df_recipes, blacklist_building, rate_expected=None, normalized=True):
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
            rate=rate_base
        elif rate_expected is not None:
            rate=rate_base/rate_expected
        else:
            rate=1

        rows.loc[index,"rate_out_1"] /= rate
        rows.loc[index,"rate_out_2"] /= rate
        rows.loc[index,"rate_in_1"] /= rate
        rows.loc[index,"rate_in_2"] /= rate
        rows.loc[index,"rate_in_3"] /= rate
        rows.loc[index,"rate_in_4"] /= rate
        item_rate.append(rate_base)
    rows["rate_base_item_selected"] = item_rate

    for building in blacklist_building:
        rows = rows[rows["building"] != building]

    return rows


def extract_items(rows, items_to_avoid):
    items = list(rows["item_in_1"])+list(rows["item_in_2"])+list(rows["item_in_3"])+list(rows["item_in_4"])
    items = list(set(items))
    items = [e for e in items if e not in items_to_avoid and e is not None]
    return items


def get_rec_recipes(item_name, df_recipes, blacklist, normalized=True):
    items_done = []
    recipes = {}
    items_todo = [item_name]
    while len(items_todo) != 0:
        item_todo = items_todo.pop()
        items_done.append(item_todo)
        if item_todo not in blacklist:
            rows = get_recipes(item_todo, df_recipes, blacklist_building=["Packager"], normalized=normalized)
            recipes[item_todo] = rows
            items_todo += extract_items(rows, items_done)
        else:
            recipes[item_todo] = None
    return recipes


def get_raws(rec_recipes):
    items_raw = []
    for item in [*rec_recipes]:
        rows = rec_recipes[item]
        if rows is None or len(rows) == 0:
            items_raw.append(item)
    return items_raw


def create_raws_recipes(item_name, df_recipes, blacklist, raws_forced):
    recipes = get_rec_recipes(item_name, df_recipes, blacklist, normalized=True)

    res = [{"recipes_list":[], "raws":{item_name: 1}}]
    res_done = []
    items = [item_name]
    items_raw = get_raws(recipes)
    items_raw += raws_forced
    print(items_raw)

    is_change = True
    it = 0
    while not (len(items)==0 or it > 1000 or not is_change):
        is_change = False
        print("------------------------------------------------------------------------------------", it)
        print(items)
        print(len(res))
        # for index, dict_ in enumerate(res):
        #     print(index, dict_)

        it += 1

        new_items = []
        j_loop = 0
        j_noloop = 0
        for item in items:
            print(item)
            rows = recipes[item]

            # get items with normalized rates to produce item
            item_recipes_items = []
            for index, row in rows.iterrows():
                item_recipe_items = {}
                if row["item_in_1"] is not None:
                    item_recipe_items[row["item_in_1"]] = row["rate_in_1"]
                if row["item_in_2"] is not None:
                    item_recipe_items[row["item_in_2"]] = row["rate_in_2"]
                if row["item_in_3"] is not None:
                    item_recipe_items[row["item_in_3"]] = row["rate_in_3"]
                if row["item_in_4"] is not None:
                    item_recipe_items[row["item_in_4"]] = row["rate_in_4"]
                new_items += list(item_recipe_items.keys())
                item_recipes_items.append({"name":row["name"], "items":item_recipe_items})
            
            for i in range(len(res)):
                dict_items = res[i]
                #print(dict_items, i, len(res), "__________________", it)
                if item in dict_items["raws"].keys():
                    for j, item_recipe_items in enumerate(item_recipes_items):
                        #print(j)

                        dict_items_copy = copy.deepcopy(dict_items)
                        if item_recipe_items["name"] not in dict_items_copy["recipes_list"]:
                            is_change = True
                            dict_items_copy["recipes_list"].append(item_recipe_items["name"])
                        else:
                            continue

                        rate_item = dict_items_copy["raws"].pop(item)
                        for new_item in item_recipe_items["items"].keys():
                            if new_item in dict_items_copy["raws"].keys():
                                dict_items_copy["raws"][new_item] += rate_item*item_recipe_items["items"][new_item]
                            else:
                                dict_items_copy["raws"][new_item] = rate_item*item_recipe_items["items"][new_item]
                        if j == 0:
                            res[i] = dict_items_copy
                        else:
                            res.append(dict_items_copy)
                        #print(dict_items_copy)

            index_res_to_del = []
            for i in range(len(res)):
                dict_items = res[i]
                is_done = True
                for e in dict_items["raws"].keys():
                    if e not in items_raw:
                        is_done = False
                        break
                if is_done:
                    res_done.append(dict_items)
                    index_res_to_del.append(i)
            index_res_to_del.sort(reverse=True)
            for i in index_res_to_del:
                del res[i]

            print(len(res_done), "|", len(res))

        items = [e for e in list(np.unique(new_items)) if e not in items_raw]
    print("######################################################")
    print(items)
    print(is_change)
    print(len(res))

    # for index, dict_ in enumerate(res):
    #     print(index, dict_)

    return res_done
