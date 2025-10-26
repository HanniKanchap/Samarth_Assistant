import requests
import pandas as pd
from io import StringIO
from itertools import product
import streamlit as st

data_key = st.secrets["DATA_API_KEY"]
def fetch_crop_data(filters, api_key = data_key):
    base_url = "https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de"

    # Normalize all filter values to lists
    normalized_filters = {
        key: value if isinstance(value, list) else [value]
        for key, value in filters.items() if value is not None
    }

    # Generate all combinations of filter values
    keys = list(normalized_filters.keys())
    combinations = list(product(*[normalized_filters[k] for k in keys]))

    all_data = []

    for combo in combinations:
        combo_filters = dict(zip(keys, combo))
        filter_str = "&".join([f"filters[{k}]={v}" for k, v in combo_filters.items()])
        url = f"{base_url}?api-key={api_key}&format=csv&{filter_str}&limit=2000"

        response = requests.get(url)
        print(f"Fetching: {url}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200 and response.text.strip():
            try:
                df = pd.read_csv(StringIO(response.text))
                all_data.append(df)
            except Exception as e:
                print(f"Error reading CSV: {e}")
        else:
            print("No data or bad response.")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

#print(fetch_crop_data({'crop_year':[2010,2015],'state_name':'Haryana','crop':'Wheat'}))