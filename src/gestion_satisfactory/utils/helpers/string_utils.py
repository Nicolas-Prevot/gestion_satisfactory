def display_name_to_table_name(display_name: str) -> str:
    """
    Convert a display name to a table name by encoding it.

    Parameters
    ----------
    display_name : str
        The display name to convert.

    Returns
    -------
    str
        The encoded table name prefixed with 'factory_planner_'.

    """
    table_name = display_name.encode('utf-8').hex()
    return f'factory_planner_{table_name}'


def table_name_to_display_name(table_name: str) -> str:
    """
    Convert a table name back to the display name by decoding it.

    Parameters
    ----------
    table_name : str
        The table name to convert.

    Returns
    -------
    str
        The decoded display name.

    """
    display_name = table_name[len("factory_planner_"):]
    display_name = bytes.fromhex(display_name).decode('utf-8')
    return display_name
