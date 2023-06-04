from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import requests
import re

def get_item_names_from_url(URL, id_tag='mw-pages'):
    """
    Returns a Soup of the Items page from the Satisfactory Wiki.
    """
    # Navigate to source URL
    items_page = requests.get(URL)

    # Setup Strainer for specific tag
    only_item_names = SoupStrainer(id=id_tag)

    # Extract html within the id_tag as Soup
    items_soup = BeautifulSoup(items_page.content, 'html.parser', parse_only=only_item_names)
    
    return items_soup

def get_list_of_item_names(items_soup):
    """
    Returns list of URL extensions for all items in the game.
    """
    # Find all alphabetical listings for items
    all_item_tags = items_soup.find_all('li')

    # Extract link locations for all items
    all_item_names = [i.a.get('href') for i in all_item_tags]

    return all_item_names

def filter_item_names(items_URL_extensions, filter_string='/[a-zA-Z]{2}$|^/%'):
    """
    Returns scraped URL extensions after filtering out non-crafting related items.
    TODO: Have these items in a separate file in the future.
    """

    # List of URLs to explicitly exclude
    blacklist = [
                    '/wiki/Cup', 
                    '/wiki/Vines', 
                    '/wiki/Statue',
                    '/wiki/HUB_Parts', 
                    '/wiki/Hard_Drive',
                    '/wiki/Somersloop', 
                    '/wiki/FICSIT_Coupon', 
                    '/wiki/Mercer_Sphere',
                    '/wiki/Quantum_Computer',
                    '/wiki/Superposition_Oscillator',
                    '/wiki/%EC%B2%A0_%EC%A3%BC%EA%B4%B4',
                    '/wiki/User:SignpostMarv/Draft/Hard_Drive',
                    '/wiki/Alien_Carapace',
                    '/wiki/Alien_Organs',
                    '/wiki/Alien_Remains',

                ]

    # List of URLs that are not on the all_items_URL (All craftable fluids atm.)
    whitelist = [
                    '/wiki/Fuel',
                    '/wiki/Turbofuel',
                    '/wiki/Nitric_Acid',
                    '/wiki/Nitrogen_Gas',
                    '/wiki/Sulfuric_Acid',
                    '/wiki/Liquid_Biofuel',
                    '/wiki/Alumina_Solution',
                    '/wiki/Heavy_Oil_Residue',
                ]

    filtered_items_URL_extensions = [item_name for item_name in items_URL_extensions if re.search(filter_string, item_name) is None]
    filtered_items_URL_extensions = [item_name for item_name in filtered_items_URL_extensions if item_name not in blacklist]
    filtered_items_URL_extensions = filtered_items_URL_extensions + whitelist

    return filtered_items_URL_extensions

def get_all_item_URLs():
    """
    Returns all available items' URL extensions available on the Satisfactory Wiki.
    """
    # Specify URL to fetch item names from
    all_items_URL = 'https://satisfactory.gamepedia.com/Category:Items'

    # Get soup of specified URL
    items_page_soup = get_item_names_from_url(all_items_URL, 'mw-pages')

    # Get list of item URL extensions from Soup
    items_URL_extensions = get_list_of_item_names(items_page_soup)

    # Filter item URLs list to exclude problematic instances
    filtered_items_URL_extensions = filter_item_names(items_URL_extensions)

    return filtered_items_URL_extensions