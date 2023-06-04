from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import requests
import re
import pandas as pd
import shutil
from tqdm import tqdm

def get_recipe_name(table_td):
    """
    Return name of recipe from Soup.
    """
    return str(table_td.contents[0])

def get_recipe_rate(string):
    """
    Return item input/output rate from string.
    """
    return float(re.match('[0-9]*[.]*[0-9]*', string).group(0))

def get_input_output(table_td):
    """
    Return list of items and rates from given table.
    """
    items_list = []
    rates_list = []
    urls_img_list = []

    while table_td:
        try:
            items_list.append(space_2_underscore(table_td.div.div.a.get('title')))
            rates_list.append(get_recipe_rate(table_td.div.next_sibling.string))

            url = table_td.div.div.a.img.get('data-src')
            if url is None:
                url = table_td.div.div.a.img.get('src')
            url = url.split(".png")[0]+".png"
            urls_img_list.append(url)
        except:
            break
        table_td = table_td.next_sibling
    return [items_list, rates_list, urls_img_list]

def get_recipe_inputs(table_td):
    """
    Return list of all input names, list of all input rates.
    """
    return get_input_output(table_td)

def get_recipe_outputs(table_td):
    """
    Return list of all output names, list of all output rates.
    """
    return get_input_output(table_td)

def get_building(table_td):
    """
    Return the building recipe is made in.
    """
    try:
        url = get_all_URLs_to_scrape([table_td.span.a.get('href')])[0]
        name = space_2_underscore(table_td.span.a.get('title'))
        return name, url
    except:
        return None, None

def get_prereq(table_td):
    """
    Return what prerequisite exists for recipe unlock.
    """
    return str(table_td.span.text)

def get_is_alternate(table_td):
    """
    Return if the recipe is an alternate recipe (locked by default).
    """
    return True if table_td.br else False

def extract_product(extension: str):
    """
    Return full product name from URL extension.
    """
    return re.search('[a-zA-Z_-]+$', extension)[0]

def get_recipe_rows(recipe_soup):
    """
    Return non-header rows from crafting table on the item's Wiki page soup.
    """
    # Get all rows for recipe page
    try:
        crafting_table = recipe_soup.find_all(class_='wikitable')[0]
    except:
        raise Exception("Problem parsing wiki page soup.")

    crafting_rows = crafting_table.find_all('tr')

    # Select all non-header rows
    non_header_rows = crafting_rows[1:]

    return non_header_rows


def underscore_2_space(string: str):
    """
    Return string with underscores replaced by spaces.
    """
    return re.sub('[_]', ' ', string)


def space_2_underscore(string: str):
    """
    Return string with underscores replaced by spaces.
    """
    return re.sub(' ', '_', string)


def get_all_URLs_to_scrape(extensions_list):
    """
    Return list of full item URLs for scraping.
    """   
    base_URL = 'https://satisfactory.fandom.com'

    return [base_URL + extension for extension in extensions_list]
    

def get_recipe_soup(recipe_URL: str):
    """
    Return Soup of given URL.
    """
    # Get HTML of recipe page
    recipe_page = requests.get(recipe_URL)
    
    # Only parse and soup-ify the recipes table
    only_recipe_table = SoupStrainer(class_='wikitable')

    recipe_soup = BeautifulSoup(recipe_page.content, 'html.parser', parse_only=only_recipe_table)

    return recipe_soup


def get_building_soup(building_URL: str):
    """
    Return Soup of given URL.
    """
    # Get HTML of recipe page
    building_page = requests.get(building_URL)
    
    only_building_table = SoupStrainer('aside')

    building_soup = BeautifulSoup(building_page.content, 'html.parser', parse_only=only_building_table)

    return building_soup


def scrape_recipe_page(recipes_soup):
    """
    Return Coproduct Recipes list for given Wiki page Soup.
    """
    items = {"name":[],"solid":[], "url_img":[]}
    buildings = {"name":[], "base_power_use":[], "url_img":[]}
    recipes = {"name":[], "alternate":[], "building":[],
               "item_in_1":[],"rate_in_1":[],
               "item_in_2":[],"rate_in_2":[],
               "item_in_3":[],"rate_in_3":[],
               "item_in_4":[],"rate_in_4":[],
               "item_out_1":[],"rate_out_1":[],
               "item_out_2":[],"rate_out_2":[]}

    # Select all non-header rows
    select_rows = get_recipe_rows(recipes_soup)

    # Define function-internal lists
    temp_inputs = []
    temp_irates = []
    temp_inputs_img = []
    temp_outputs = []
    temp_orates = []
    temp_ouputs_img = []

    # For each row in table (besides column names)
    for i in range(len(select_rows)):

        # Get first row's input item names and rates listed on HTML structure with 'class' attr
        if select_rows[i].has_attr('class'):

            # Get name for recipe, always index 0
            recipe_name = get_recipe_name(select_rows[i].find_all('td')[0])

            # Get if recipe is alt, always index 0
            recipe_is_alt = get_is_alternate(select_rows[i].find_all('td')[0])

            # Get primary row input values. always index 1+
            inps, irts, in_urls_img = get_recipe_inputs(select_rows[i].find_all('td')[1])
            temp_inputs = inps
            temp_irates = irts
            temp_inputs_img = in_urls_img

            # Get proper index for building info location in row
            if len(temp_inputs) < 2:
                building_index = 2

            else:
                building_index = 3

            # If exists, get first row's secondary inputs listed on HTML structure with no 'class' attr
            try:
                if not select_rows[i+1].has_attr('class'):

                    # Append secondary row input values to primary ones
                    inps, rts, in_urls_img = get_recipe_inputs(select_rows[i+1].find_all('td')[0])
                    temp_inputs += inps
                    temp_irates += rts
                    temp_inputs_img += in_urls_img

            except:
                pass

            # Get building info
            recipe_building, url_building = get_building(select_rows[i].find_all('td')[building_index])
            # print(recipe_building)

            # Get outputs for recipe, one index up from building
            outs, orts, out_urls_img = get_recipe_outputs(select_rows[i].find_all('td')[building_index+1])
            temp_outputs = outs
            temp_orates = orts
            temp_ouputs_img = out_urls_img
        
        # If hit row with no primary values, skip
        else:
            continue

        for item_name, url in zip(temp_inputs, temp_inputs_img):
            if item_name not in items["name"]:
                items["name"].append(item_name)
                items["solid"].append(None)
                items["url_img"].append(url)
        
        for item_name, url in zip(temp_outputs, temp_ouputs_img):
            if item_name not in items["name"]:
                items["name"].append(item_name)
                items["solid"].append(None)
                items["url_img"].append(url)
        
        if recipe_building not in buildings["name"]:
            buildings["name"].append(recipe_building)
            buildings["base_power_use"].append(None)
            buildings["url_img"].append(url_building)

        temp_inputs = temp_inputs + [None]*(4-len(temp_inputs))
        temp_irates = temp_irates + [None]*(4-len(temp_irates))
        temp_outputs = temp_outputs + [None]*(2-len(temp_outputs))
        temp_orates = temp_orates + [None]*(2-len(temp_orates))
        
        recipes["name"].append(recipe_name)
        recipes["alternate"].append(recipe_is_alt)
        recipes["building"].append(recipe_building)
        recipes["item_in_1"].append(temp_inputs[0])
        recipes["rate_in_1"].append(temp_irates[0])
        recipes["item_in_2"].append(temp_inputs[1])
        recipes["rate_in_2"].append(temp_irates[1])
        recipes["item_in_3"].append(temp_inputs[2])
        recipes["rate_in_3"].append(temp_irates[2])
        recipes["item_in_4"].append(temp_inputs[3])
        recipes["rate_in_4"].append(temp_irates[3])
        recipes["item_out_1"].append(temp_outputs[0])
        recipes["rate_out_1"].append(temp_orates[0])
        recipes["item_out_2"].append(temp_outputs[1])
        recipes["rate_out_2"].append(temp_orates[1])

    return items, buildings, recipes


def scrape_building_page(building_soup):
    img_soup = building_soup.find_all('img')[0]
    url_img = img_soup.get("src")
    url_img = url_img.split(".png")[0]+".png"

    try:
        def has_class(tag):
            return tag.has_attr('data-source') and tag['data-source'] == "powerUsage"
        power_soup = building_soup.find_all(has_class)[0]
        base_power_use = power_soup.div.get_text()
    except:
        def has_class(tag):
            return tag.has_attr('data-source') and tag['data-source'] == "powerGenerated"
        power_soup = building_soup.find_all(has_class)[0]
        base_power_use = "-" + power_soup.div.get_text()

    return base_power_use, url_img


def save_img(name, url, path):
    r = requests.get(url, stream=True) #Get request on full_url
    path = f"{path}{name}.png"
    if r.status_code == 200:                     #200 status code = OK
        with open(path, 'wb') as f: 
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    return path


def get_all_dfs(extensions_list: list, config):

    # Get list of item name URLs, convert to full URLs for scraping.
    all_item_URLs = get_all_URLs_to_scrape(extensions_list)
    print("\nall_item_URLs")
    print(len(all_item_URLs), all_item_URLs)

    # Get Soup list from all item URLs.
    all_recipe_soups = [get_recipe_soup(recipe_page) for recipe_page in tqdm(all_item_URLs)]

    # Init dict for futur dataFrames
    df_items = {"name":[],"solid":[], "url_img":[]}
    df_buildings = {"name":[], "base_power_use":[], "url_img":[]}
    df_recipes = {"name":[], "alternate":[], "building":[],
               "item_in_1":[],"rate_in_1":[],
               "item_in_2":[],"rate_in_2":[],
               "item_in_3":[],"rate_in_3":[],
               "item_in_4":[],"rate_in_4":[],
               "item_out_1":[],"rate_out_1":[],
               "item_out_2":[],"rate_out_2":[]}

    # Complete dicts from pages soup
    for recipe_soup in tqdm(all_recipe_soups):
        items, buildings, recipes = scrape_recipe_page(recipe_soup)
        for key in df_items:
            df_items[key] += items[key]
        for key in df_buildings:
            df_buildings[key] += buildings[key]
        for key in df_recipes:
            df_recipes[key] += recipes[key]

    # Convert dicts to DataFrames 
    df_items = pd.DataFrame.from_dict(df_items)
    df_buildings = pd.DataFrame.from_dict(df_buildings)
    df_recipes = pd.DataFrame.from_dict(df_recipes)

    # Remove undesired rows
    df_items.drop_duplicates(inplace=True, ignore_index=True)
    df_buildings.drop_duplicates(inplace=True, ignore_index=True)
    df_buildings.dropna(how='all', inplace=True, ignore_index=True)
    df_recipes.drop_duplicates(inplace=True, ignore_index=True)

    print(df_items)
    print(df_buildings)
    print(df_recipes)

    # Download images and change url with path saved
    for i, (name, url) in tqdm(enumerate(zip(df_items.name, df_items.url_img)), total=len(df_items.name)):
        path_img = save_img(name, url, config.project.path_imgs)
        df_items.url_img[i] = path_img

    # Collect soups from building urls
    all_buildings_soups = []
    for building_page in tqdm(df_buildings.url_img):
        building_soup = get_building_soup(building_page)
        all_buildings_soups.append(building_soup)

    # download images and change url with path saved
    for i, (building_name, building_soup) in tqdm(enumerate(zip(df_buildings.name, all_buildings_soups)), total=len(df_buildings.name)):
        base_power_use, url_img = scrape_building_page(building_soup)
        path_img = save_img(building_name, url_img, config.project.path_imgs)
        df_buildings.base_power_use[i] = base_power_use
        df_buildings.url_img[i] = path_img
    
    print(df_items)
    print(df_buildings)
    print(df_recipes)

    return df_items, df_buildings, df_recipes






