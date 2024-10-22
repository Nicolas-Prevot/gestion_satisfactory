def display_name_to_table_name(display_name):
    # Replace spaces with underscores and make the string lowercase
    table_name = display_name.encode('utf-8').hex()
    return f'factory_planner_{table_name}'

def table_name_to_display_name(table_name):
    # Split the table name by underscores and skip the first two words
    display_name = table_name[len("factory_planner_"):]
    display_name = bytes.fromhex(display_name).decode('utf-8')
    return display_name
