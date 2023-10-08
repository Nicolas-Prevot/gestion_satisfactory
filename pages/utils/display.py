import streamlit as st

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
    for item in results_consommation:
        if (item in list(results_production.keys())):
            result = results_consommation[item] + results_production[item]
            if (result < 0):
                results_negative[item] = result
            else:
                results_positive[item] = result
        else:
            results_negative[item] = results_consommation[item]

    for item in results_production:
        if (item not in list(results_consommation.keys())):
            results_positive[item] = results_production[item]

    st.write(f"⚡ {power_usage} MW ⚡")

    def write_cols():
        col1, col2 = st.columns(2)
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
                                
    if (display_in_expander):
        with st.expander("Results"):
            write_cols()
    else:
        write_cols()


                            