from streamlit_agraph import agraph, Node, Edge, Config

from .recipes_search import extract_items


def create_genealogy_graph(recipes, item_to_img, blacklist):
    items = [*recipes]
    nodes = []
    edges = []

    for item in items:
        #if item not in blacklist:
        nodes.append(Node(id=item,
                        label=item,
                        size=15,
                        image=item_to_img[item],
                        shape="circularImage"))
    
    for item in items:
        if item not in blacklist:
            rows = recipes[item]
            items_for_item = extract_items(rows, [])
            for item2 in items_for_item:
                if item2 in items:# and item2 not in blacklist:
                    edges.append(Edge(source=item2, target=item))


    config = Config(width=750,
                    height=950,
                    directed=True, 
                    physics=True, 
                    hierarchical=False
                    )

    return nodes, edges, config

