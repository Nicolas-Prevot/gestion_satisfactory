import numpy as np
from pulp import *


def get_items(df_recipes, df_items):
    items = list(set(list(df_recipes["item_out_1"])+list(df_recipes["item_out_2"])))
    items = [e for e in items if e is not None]
    exceptions = ["Crude_Oil", "Coal", "Water", "Nitrogen_Gas"]
    for e in exceptions:
        items.remove(e)

    all_items = df_items["name"]

    items_raw = list(set(all_items) - set(items))
    return items, items_raw


def get_recipes_vect(df_recipes, items, items_raw):
    R = []
    Rp = []
    recipe_names = []
    for row in df_recipes.iterrows():
        row = row[1]
        if row["building"] == "Packager":
            continue
        if row["name"] == "Charcoal":
            continue
        if row["building"] is not None:

            # print("--------------------------------")
            # print(row["name"])

            R_j = [0]*len(items)
            Rp_j = [0]*len(items_raw)

            for i in range(2):
                item_out = row[f"item_out_{i+1}"]
                if item_out is not None:
                    if item_out in items:
                        index = items.index(item_out)
                        R_j[index] = row[f"rate_out_{i+1}"]
                        # print(item_out, R_j[index])
                    else:
                        index = items_raw.index(item_out)
                        Rp_j[index] = row[f"rate_out_{i+1}"]
                        # print(item_out, Rp_j[index])
            
            for i in range(4):
                item_in = row[f"item_in_{i+1}"]
                if item_in is not None:
                    if item_in in items:
                        index = items.index(item_in)
                        R_j[index] = -row[f"rate_in_{i+1}"]
                        # print(item_in, R_j[index])
                    else:
                        index = items_raw.index(item_in)
                        Rp_j[index] = -row[f"rate_in_{i+1}"]
                        # print(item_in, Rp_j[index])
                        
            recipe_names.append(row["name"])

            # print(R_j, Rp_j)

            R.append(R_j)
            Rp.append(Rp_j)
    return np.array(R), np.array(Rp), recipe_names


"""
df_items = load_df("items")
df_recipes = load_df("recipes")
# df_buildings = load_df("buildings")

items, items_raw = get_items(df_recipes, df_items)

R, Rp, recipe_names = get_recipes_vect(df_recipes, items, items_raw)

weight_raw_items_dict = {'Raw_Quartz':2,
                        'Bauxite':3,
                        'Crude_Oil':0.5,
                        'Iron_Ore':1,
                        'Coal':1,
                        'Uranium':10,
                        'Sulfur':1,
                        'Nitrogen_Gas':2,
                        'Water':0,
                        'Caterium_Ore':2,
                        'Limestone':1,
                        'Copper_Ore':1,

                        'Wood':1,
                        'Blue_Power_Slug':1,
                        'Plasma_Spitter_Remains':1,
                        'Purple_Power_Slug':1,
                        'Flower_Petals':1,
                        'Stinger_Remains':1,
                        'Yellow_Power_Slug':1,
                        'Mycelia':1,
                        'Hog_Remains':1,
                        'Hatcher_Remains':1,
                        'Leaves':1,
                        }
"""


def get_best_production(item, items, items_raw, R, Rp, recipe_names, weight_raw_items_dict, quantity=100):
    # items_exceptions = []
    # index_items_exceptions = [items.index(e) for e in items_exceptions]

    if item not in items:
        raise Exception("'item' must be in the list 'items'!")

    index_item_r = items.index(item)

    set_M = range(0, len(recipe_names))

    weight_raw_items = [weight_raw_items_dict[e] for e in items_raw]

    # Generate proble, & Create variables
    prob = LpProblem("combination_recipes", LpMinimize)
    Lmbda = pulp.LpVariable.dicts("Lmbda", set_M, cat='Continuous', lowBound=0)

    # Make up an objective
    prob += -lpSum([Lmbda[j]*np.sum(Rp[j]*weight_raw_items) for j in set_M])

    # Apply constraints
    for i in range(np.shape(R)[1]):
        # if i in index_items_exceptions:
        #     continue
        thresh = 0
        if i == index_item_r:
            thresh = quantity
        prob += lpSum([Lmbda[j]*R[j, i] for j in set_M]) >= thresh

    # Solve problem
    status = prob.solve()

    status_solution = LpStatus[status]

    Lmbda_soln = np.array([Lmbda[j].varValue for j in set_M])

    return Lmbda_soln, status_solution