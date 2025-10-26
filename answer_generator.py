from groq_llama_agent import extract_entities, gpt_response
from fetch_crop_data import fetch_crop_data
import pandas as pd
from itertools import product
import re

def generate_answer(question):

    crop_prompt = f"""
You are a data analyst. Extract structured filters and intent from the following question:
\"{question}\"
Important - Give the following JSON if questions is asking crop or production,agriculture related query , else return None.
Return a JSON object with exactly these keys:
- state_name
- crop_year (if a range is mentioned like 2019–2020, expand it to a list of individual years. If no year is mentioned, default to [2010-2024] and expand it to individual years)
- season
- crop (only include specific crop names like Wheat, Barley, Jute, etc. If vague terms like 'top 3 crops' or 'most produced crops' are used, set this to null)
- district_name

Do not include any additional parameters. Only return the JSON. Do not include any explanation or formatting outside the JSON block.
"""

    crop_entities = extract_entities(crop_prompt)
    print("Crop Entities:", crop_entities)

    # Normalize crop filters to support multiple values
    crop_df = pd.DataFrame()
    if crop_entities:
        crop_filters = {
            k: v if isinstance(v, list) else [v] for k, v in crop_entities.items() if v is not None
        }
        # Fetch crop data for all combinations
        keys = list(crop_filters.keys())
        combinations = list(product(*[crop_filters[k] for k in keys]))
        crop_dfs = []
        for combo in combinations:
            combo_dict = dict(zip(keys, combo))
            df = fetch_crop_data(combo_dict)
            if not df.empty:
                crop_dfs.append(df)
        crop_df = pd.concat(crop_dfs, ignore_index=True) if crop_dfs else pd.DataFrame()

    rain_prompt = f"""
You are a data analyst working with Indian rainfall data from IMD.
Important - Give the following JSON if questions is asking climate related or rainfall related query , else return None.
Extract structured filters from the following question:
\"{question}\"

Return a JSON object with exactly these keys:
- subdivision (match using substring, e.g., 'Delhi' should match 'East Delhi' and default is None)
- rainfall_year (if a range is mentioned like 2019–2020, expand it to a list of individual years. If no year is mentioned, default to [2014, 2015, 2016, 2017] ,if given last N Years , consider years from 2017 to 2017-N or handle the cases like decade(10 years from 2017 backwards) and others)
- rainfall_metric (choose from: JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC, ANNUAL, JF, MAM, JJAS, OND)

Do not include any additional parameters. Only return the JSON. Do not include any explanation or formatting outside the JSON block.
"""

    rain_entities = extract_entities(rain_prompt)
    print("Rainfall Entities:", rain_entities)

    # Load rainfall data
    rain_df = pd.DataFrame()
    if rain_entities:
        rain_df = pd.read_csv('./data/rainfall_data.csv')

        # Filter rainfall data for multiple subdivisions and years
        subdivisions = rain_entities.get("subdivision", [])
        years = rain_entities.get("rainfall_year", [])
        if isinstance(subdivisions, str):
            subdivisions = [subdivisions]
        if isinstance(years, int):
            years = [years]

        filtered_rain_dfs = []
        if subdivisions:
            for sub in subdivisions:
                pattern = re.escape(sub)
                df = rain_df[rain_df["SUBDIVISION"].str.contains(pattern, case=False, na=False)]
                if years:
                    df = df[df["YEAR"].isin(years)]
                if not df.empty:
                    filtered_rain_dfs.append(df)
        rain_df = pd.concat(filtered_rain_dfs, ignore_index=True) if filtered_rain_dfs else pd.DataFrame()
            
            
    return (gpt_response(question, crop_df, rain_df),crop_df,rain_df)
