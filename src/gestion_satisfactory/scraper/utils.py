from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import requests
import re
import pandas as pd
import shutil
from tqdm import tqdm


# For streamlit display
class sttqdm:
    def __init__(self, iterable, title=None, total=-1, streamlit_display=False):
        self.streamlit_display = streamlit_display
        if (total < 0):
            self.length = len(iterable)
        else:
            self.length = total

        if (self.streamlit_display):
            import streamlit as st

            if title:
                st.write(title)
            self.prog_bar = st.progress(0)
            self.iterable = iterable
            self.i = 0

        self.tqdm = tqdm(iterable, title, self.length)

    def __iter__(self):
    
        for obj in self.tqdm:
            yield obj
            if (self.streamlit_display):
                self.i += 1
                current_prog = self.i / self.length
                self.prog_bar.progress(current_prog)
        if (self.streamlit_display):
            self.prog_bar.empty()


def save_img(name, url, path):
    r = requests.get(url, stream=True)  # Get request on full_url
    path = f"{path}{name}.png"
    if r.status_code == 200:  # 200 status code = OK
        with open(path, 'wb') as f: 
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    return path


def normalize_text(text):
    return ''.join(e for e in text if e.isalnum()).lower()


def parse_building_description(soup):
    info = {
        'image_path': None,
        'unlocked_by': None,
        'class_name': None,
        'power_usage': None,
        'overclockable': None,
        'conveyor_inputs': 0,
        'conveyor_outputs': 0,
        'pipeline_inputs': 0,
        'pipeline_outputs': 0,
        'width': None,
        'length': None,
        'height': None,
        'area': None,
        'ingredients': {}
    }

    label_mapping = {
        'unlockedby': 'unlocked_by',
        'classname': 'class_name',
        'powerusage': 'power_usage',
        'overclockable': 'overclockable',
        'conveyorinputs': 'conveyor_inputs',
        'conveyoroutputs': 'conveyor_outputs',
        'pipelineinputs': 'pipeline_inputs',
        'pipelineoutputs': 'pipeline_outputs',
        'width': 'width',
        'length': 'length',
        'height': 'height',
        'area': 'area'
    }

    numeric_keys = {
        'power_usage',
        'conveyor_inputs',
        'conveyor_outputs',
        'pipeline_inputs',
        'pipeline_outputs',
        'width',
        'length',
        'height',
        'area'
    }

    # Extract image path
    figure_tag = soup.find('figure', class_='pi-item pi-media pi-image')
    if figure_tag:
        img_tag = figure_tag.find('img')
        if img_tag and 'src' in img_tag.attrs:
            info['image_path'] = img_tag['src']

    # Find the ingredients section
    ingredients_section = None
    for h2_tag in soup.find_all('h2'):
        text = h2_tag.get_text(strip=True)
        normalized_text = normalize_text(text)
        if 'ingredients' in normalized_text:
            ingredients_section = h2_tag
            break
    ingredients_parent_section = None
    if ingredients_section:
        ingredients_parent_section = ingredients_section.find_parent('section')

    data_divs = soup.find_all('div', class_='pi-data')

    for data_div in data_divs:
        # Skip data_divs under the ingredients section
        if ingredients_parent_section and ingredients_parent_section in data_div.parents:
            continue
        label_tag = data_div.find('h3', class_='pi-data-label')
        value_tag = data_div.find('div', class_='pi-data-value')
        if label_tag and value_tag:
            label = label_tag.get_text(separator=' ', strip=True)
            value = value_tag.get_text(separator=' ', strip=True)
            # Normalize label
            label_norm = normalize_text(label)
            # Map label to key
            key = label_mapping.get(label_norm)
            if key:
                if key in numeric_keys:
                    # Extract numeric part
                    num_match = re.search(r'[\d.]+', value)
                    if num_match:
                        num_str = num_match.group()
                        # Convert to int or float
                        if '.' in num_str:
                            num_value = float(num_str)
                        else:
                            num_value = int(num_str)
                        info[key] = num_value
                    else:
                        info[key] = None  # No number found
                else:
                    info[key] = value

    # Process ingredients
    if ingredients_parent_section:
        ingredient_items = ingredients_parent_section.find_all('div', class_='pi-data')
        pattern = re.compile(r'(\d+)\s*×\s*(.*)')
        for item in ingredient_items:
            value_tag = item.find('div', class_='pi-data-value')
            if value_tag:
                text = value_tag.get_text(separator=' ', strip=True)
                match = pattern.match(text)
                if match:
                    amount = int(match.group(1))
                    ingredient = match.group(2).strip()
                    info['ingredients'][ingredient] = amount

    return info


def parse_building_recipes(soup):
    recipes = []

    # Get all rows except the header
    rows = soup.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 5:
            continue  # Skip rows that don't have enough columns

        # Extract recipe name
        recipe_name = cols[0].get_text(strip=True)

        # Extract is alternate
        recipe_alternate = cols[0].find('span', class_='recipe-alternate') is not None

        # Extract ingredients
        ingredients = []
        ingredients_div = cols[1].find('div', class_='recipe-items')
        if ingredients_div:
            ingredient_items = ingredients_div.find_all('div', class_='recipe-item')
            for item in ingredient_items:
                amount_tag = item.find('span', class_='item-amount')
                name_tag = item.find('span', class_='item-name')
                img_tag = item.find('a').find('img') if item.find('a') else None

                amount_text = amount_tag.get_text(strip=True) if amount_tag else ''
                amount = int(re.search(r'(\d+)', amount_text).group(1)) if amount_text else None
                name = name_tag.get_text(strip=True) if name_tag else ''
                img_path = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

                ingredients.append({
                    'name': name,
                    'amount': amount,
                    'image_path': img_path
                })

        # Extract duration and power consumption
        duration_cell = cols[2]
        duration_text = duration_cell.get_text(separator=' ', strip=True)
        duration_match = re.search(r'(\d+\.?\d*)\s*sec', duration_text)
        duration = float(duration_match.group(1)) if duration_match else None

        # Initialize min and max consumption
        min_consumption = None
        max_consumption = None

        # Check for power consumption range in the duration cell
        consumption_match = re.search(r'(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)\s*MW', duration_text)
        if consumption_match:
            min_consumption_str = consumption_match.group(1).replace(',', '')
            max_consumption_str = consumption_match.group(2).replace(',', '')
            min_consumption = int(min_consumption_str)
            max_consumption = int(max_consumption_str)

        # Extract products
        products = []
        products_div = cols[3].find('div', class_='recipe-items')
        if products_div:
            product_items = products_div.find_all('div', class_='recipe-item')
            for item in product_items:
                amount_tag = item.find('span', class_='item-amount')
                name_tag = item.find('span', class_='item-name')
                img_tag = item.find('a').find('img') if item.find('a') else None

                amount_text = amount_tag.get_text(strip=True) if amount_tag else ''
                amount = int(re.search(r'(\d+)', amount_text).group(1)) if amount_text else None
                name = name_tag.get_text(strip=True) if name_tag else ''
                img_path = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

                products.append({
                    'name': name,
                    'amount': amount,
                    'image_path': img_path
                })

        # Extract "unlocked by" information
        unlocked_by = cols[4].get_text(separator=' ', strip=True)

        # Append the recipe data to the list
        recipes.append({
            'name': recipe_name,
            'recipe_alternate': recipe_alternate,
            'ingredients': ingredients,
            'duration': duration,
            'products': products,
            'unlocked_by': unlocked_by,
            'min_consumption': min_consumption,
            'max_consumption': max_consumption,
        })

    return recipes


def flatten_building_data(building_dict):
    flat_data = {}
    for name, data in building_dict.items():
        flat_entry = data.copy()
        # Flatten the ingredients dictionary
        ingredients = flat_entry.pop('ingredients', {})
        for i in range(1, 6):
            ingredient_key = f'ingredient_{i}'
            amount_key = f'amount_{i}'
            if i <= len(ingredients):
                ingredient_name = list(ingredients.keys())[i - 1]
                ingredient_amount = ingredients[ingredient_name]
                flat_entry[ingredient_key] = ingredient_name
                flat_entry[amount_key] = ingredient_amount
            else:
                flat_entry[ingredient_key] = None
                flat_entry[amount_key] = None
        flat_entry['name'] = name  # Add the building name for merging
        flat_data[name] = flat_entry
    return flat_data


def flatten_recipes(recipes_dict):
    items_list = []
    recipe_entries = []
    for building_name, recipes in recipes_dict.items():
        for idx, recipe in enumerate(recipes):
            flat_recipe = {
                'building_name': building_name,
                'recipe_name': recipe.get('name'),
                'recipe_alternate': recipe.get('recipe_alternate'),
                'duration': recipe.get('duration'),
                'unlocked_by': recipe.get('unlocked_by'),
                'min_consumption': recipe.get('min_consumption'),
                'max_consumption': recipe.get('max_consumption')
            }
            # Flatten ingredients
            ingredients = recipe.get('ingredients', [])
            for i in range(1, 5):  # Up to 4 ingredients
                if i <= len(ingredients):
                    ingredient = ingredients[i - 1]
                    ingredient_name = ingredient.get('name')
                    flat_recipe[f'ingredient_{i}'] = ingredient_name
                    flat_recipe[f'ingredient_amount_{i}'] = ingredient.get('amount')
                    items_list.append({'name': ingredient_name,
                                       'url': ingredient.get('image_path')})
                else:
                    flat_recipe[f'ingredient_{i}'] = None
                    flat_recipe[f'ingredient_amount_{i}'] = None
            # Flatten products
            products = recipe.get('products', [])
            for i in range(1, 3):  # Up to 2 products
                if i <= len(products):
                    product = products[i - 1]
                    product_name = product.get('name')
                    flat_recipe[f'product_{i}'] = product_name
                    flat_recipe[f'product_amount_{i}'] = product.get('amount')
                    items_list.append({'name': product_name,
                                       'url': product.get('image_path')})
                else:
                    flat_recipe[f'product_{i}'] = None
                    flat_recipe[f'product_amount_{i}'] = None
            recipe_entries.append(flat_recipe)
    return recipe_entries, items_list
