import re
import streamlit as st

MD_LEFT_ALIGNED = ":-"
MD_CENTER_ALIGNED = ":-:"
MD_RIGHT_ALIGNED = "-:"
OC_COLOR="#FF7700"
NB_BUILDING_COLOR="#00A9FF"
RATE_COLOR="#00C800"


def get_item_display(img, name, rate=0, oc=0, nb_building=0):
    string = ""
    if name is None:
        return string
    final_rate = rate*oc*nb_building
    if (rate != 0):
        string = f'<figure class="image" style="margin: 0px;"><img src="{img}" width=50px>\
                    <figcaption style="font-size: 12px;">\
                        {rate}\
                        x\
                        <span style="color:{NB_BUILDING_COLOR}">{nb_building:.2f}</span>\
                        x\
                        <span style="color:{OC_COLOR}">{oc:.2f}</span> =\
                        <br/><span style="color:{RATE_COLOR}">{final_rate:.2f}</span>\
                        <br/>{name.replace("_", " ")}\
                    </figcaption>\
                </figure>'
    else:
        string = f'<figure class="image" style="margin: 0px;"><img src="{img}" width=75px>\
                    <figcaption style="font-size: 12px;">\
                        {name}\
                    </figcaption>\
                 </figure>'
    return string
    

def get_row_text(infos):
    return f'|{infos["recipe_name"]}\
        |{"🔄" if infos["alternative"] else "🟦"}\
        |{get_item_display(infos["img_product_1"], infos["name_product_1"], infos["rate_product_1"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_product_2"], infos["name_product_2"], infos["rate_product_2"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_building"], infos["name_building"])}\
        |{get_item_display(infos["img_ingredient_1"], infos["name_ingredient_1"], infos["rate_ingredient_1"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_2"], infos["name_ingredient_2"], infos["rate_ingredient_2"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_3"], infos["name_ingredient_3"], infos["rate_ingredient_3"], infos["overclock"], infos["nb_building"])}\
        |{get_item_display(infos["img_ingredient_4"], infos["name_ingredient_4"], infos["rate_ingredient_4"], infos["overclock"], infos["nb_building"])}\
        |{infos["overclock"]}\
        |{infos["nb_building"]:.2f}|\n'


def display_recipes_frame(df_recipes, df_items, df_buildings, recipe_vars, recipe_var_to_name):

    title_line = f'|Recipe name|Alt.|Out 1|Out 2|Buidling|In 1|In 2|In 3|In 4|<span style="color:{OC_COLOR}">OC</span>|<span style="color:{NB_BUILDING_COLOR}">Nb Building</span>|'
    setup_line = f"|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_LEFT_ALIGNED}|{MD_CENTER_ALIGNED}|{MD_CENTER_ALIGNED}|"
    
    markdown_text = title_line+'\n'+setup_line+'\n'

    for var_name, amount in recipe_vars.items():
        if amount < 1e-10:
            continue
        recipe_name = recipe_var_to_name[var_name]
        infos_row = {
            "recipe_name":recipe_name,
            "nb_building":amount,
            "overclock":1,
        }

        row = df_recipes[df_recipes["recipe_name"] == recipe_name]
        duration = row["duration"].values[0]
        if len(row) != 0:
            iter_items = {"product":2,
                          "ingredient":4}
            for inout in iter_items:
                for i in range(1,iter_items[inout]+1):
                    item = row[f"{inout}_{i}"].values[0]
                    if item is None:
                        src_img = None
                        rate = None
                    else:
                        src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
                        rate = 60 * row[f"{inout}_amount_{i}"].values[0] / duration
                    infos_row[f"img_{inout}_{i}"] = src_img
                    infos_row[f"name_{inout}_{i}"] = item
                    infos_row[f"rate_{inout}_{i}"] = rate 
        
            name_building = row["building_name"].values[0]
            img_building = df_buildings[df_buildings["name"] == name_building]["web_img"].tolist()[0]
            infos_row["name_building"] = name_building
            infos_row["img_building"] = img_building
            infos_row["alternative"] = row["recipe_alternate"].values[0]
            
            markdown_text += get_row_text(infos_row)
        
    st.markdown(markdown_text, unsafe_allow_html=True)


def display_items_in_columns(df_items, items_dict, title):
    st.write(f"### {title}")
    if items_dict:
        items = list(items_dict.items())
        num_cols = 3
        cols = st.columns(num_cols)
        for idx, (item, value) in enumerate(items):
            col = cols[idx % num_cols]
            src_img = df_items[df_items["name"] == item]["web_img"].tolist()[0]
            with col:
                st.markdown(
                    f'<div style="text-align: center;">'
                    f'<img src="{src_img}" width="40px"><br>'
                    f'{item}: {value:.2f}'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.write(f"No {title.lower()} to display.")


def display_items_balance(df_recipes, df_items, raw_items, not_raw_items, recipe_vars, recipe_var_to_name):
    all_items = raw_items + not_raw_items
    items_output = dict.fromkeys(all_items, 0)

    THRESHOLD = 1e-2

    for var_name, amount in recipe_vars.items():
        if amount < THRESHOLD:
            continue
        
        recipe_name = recipe_var_to_name[var_name]
        idx = df_recipes[df_recipes["recipe_name"] == recipe_name].index[0]
        duration = df_recipes.at[idx, 'duration']
        for item in all_items:
            net_prod = (
                sum(
                    df_recipes.at[idx, f'product_amount_{l}']
                    for l in range(1, 3)
                    if df_recipes.at[idx, f'product_{l}'] == item
                )
                - sum(
                    df_recipes.at[idx, f'ingredient_amount_{k}']
                    for k in range(1, 5)
                    if df_recipes.at[idx, f'ingredient_{k}'] == item
                )
            )
            net_prod_per_minute = net_prod * 60 * amount / duration
            items_output[item] += net_prod_per_minute

    items_output = {item: value for item, value in items_output.items() if abs(value) > THRESHOLD}

    raw_items_output = {item: value for item, value in items_output.items() if item in raw_items}
    not_raw_items_output = {item: value for item, value in items_output.items() if item in not_raw_items}
            
    display_items_in_columns(df_items, raw_items_output, "Raw Items Balance")
    st.write("---")
    display_items_in_columns(df_items, not_raw_items_output, "Not Raw Items Balance")

    """for item, value in raw_items_output.items():
        if value != 0:
            st.write(item, value)

    st.write("---------------------")

    for item, value in not_raw_items_output.items():
        if value != 0:
            st.write(item, value) """


def display_results_item(df_factory_planner, df_items, display_in_expander=False):
    results_production = {}
    results_consommation = {}
    power_usage = 0
    for i, row in df_factory_planner.iterrows():
        for k in range(2):
            if (row[f"item_out_{k+1}"] is not None):
                if (row[f"item_out_{k+1}"] not in list(results_production.keys())):
                    results_production[row[f"item_out_{k+1}"]] = 0
                results_production[row[f"item_out_{k+1}"]] += float(row[f"rate_out_{k+1}"])*float(row["nb_building"])*float(row["rate/overclock"])

        for k in range(4):
            if (row[f"item_in_{k+1}"] is not None):
                if (row[f"item_in_{k+1}"] not in list(results_consommation.keys())):
                    results_consommation[row[f"item_in_{k+1}"]] = 0
                results_consommation[row[f"item_in_{k+1}"]] -= float(row[f"rate_in_{k+1}"])*float(row["nb_building"])*float(row["rate/overclock"])
        
        if (row["power_usage"] is not None):
            power_usage += float(row["power_usage"][:-3])*float(row["nb_building"])*float(row["rate/overclock"])

    results_positive = {}
    results_negative = {}
    results_negative_imports = {}
    for item in results_consommation:
        if (item in list(results_production.keys())):
            result = results_consommation[item] + results_production[item]
            if (result < 0):
                results_negative[item] = result
            else:
                results_positive[item] = result
        else:
            results_negative_imports[item] = results_consommation[item]

    for item in results_production:
        if (item not in list(results_consommation.keys())):
            results_positive[item] = results_production[item]

    st.write(f"⚡ {power_usage} MW ⚡")

    def write_cols():
        col1, col2, col3 = st.columns(3)
        with col1:
            if (len(results_positive) != 0):
                for item in results_positive:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    st.markdown(f'<img src="{df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                **<span style="color:#63ACFF">{results_positive[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)',
                                unsafe_allow_html=True)
        with col2:
            if (len(results_negative) != 0):
                for item in results_negative:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    st.markdown(f'<img src="{df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                **<span style="color:#FF5154">{results_negative[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)',
                                unsafe_allow_html=True)
        with col3:
            if (len(results_negative_imports) != 0):
                for item in results_negative_imports:
                    conso = results_consommation[item] if item in list(results_consommation.keys()) else 0
                    prod = results_production[item] if item in list(results_production.keys()) else 0
                    st.markdown(f'<img src="{df_items[df_items["name"] == item]["streamlit_path_img"].tolist()[0]}" width=40px> {item.replace("_", " ")}: \
                                **<span style="color:#FF5154">{results_negative_imports[item]}</span>** (<span style="color:#00C800">{prod}</span> | <span style="color:#FF965E">{conso}</span>)',
                                unsafe_allow_html=True)
                                
    if (display_in_expander):
        with st.expander("Results"):
            write_cols()
    else:
        write_cols()


                            