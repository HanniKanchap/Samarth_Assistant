from groq_llama_agent import extract_entities, gpt_response
from fetch_crop_data import fetch_crop_data
import pandas as pd
from itertools import product
import re

def generate_answer(question):
    def convert_years_to_financial_format(years):
        return [f"{y}-{str(y+1)[-2:]}" for y in years]

    def interpret_crop_years(raw_years):
        if not raw_years:
            return list(range(2010, 2021))  # default to 2010–2020
        if isinstance(raw_years, int):
            return [raw_years]
        return raw_years

    # Extract crop filters
    crop_prompt = f"""
You are a data analyst working with Indian agricultural production data.

Your task is to extract structured filters from the following user query:
\"{question}\"

Only respond if the query is related to crops, agriculture, or production. Otherwise, return None.

Return a JSON object with exactly these keys:
- state_name
- crop_year: If a range like "2019–2021" is mentioned, expand it to a list of individual years. If no year is mentioned, default to [2010–2020] and expand. If phrases like "last N years", "last year", "recent years", or "decade" are used, interpret them relative to 2020 (e.g., "last 3 years" → [2018, 2019, 2020]).
- season (if given all that means donr specify anything keep it none)
- crop: Include only specific crop names like Wheat, Barley, Jute, etc. If vague terms like "top crops" or "most produced" are used, set this to null.
- district_name

Do not include any explanation or formatting outside the JSON block.
"""
    crop_entities = extract_entities(crop_prompt)
    print("Crop Entities:", crop_entities)

    crop_df = pd.DataFrame()
    if crop_entities:
        crop_filters = {
            k: v if isinstance(v, list) else [v]
            for k, v in crop_entities.items() if v is not None
        }
        keys = list(crop_filters.keys())
        combinations = list(product(*[crop_filters[k] for k in keys]))
        crop_dfs = []
        for combo in combinations:
            combo_dict = dict(zip(keys, combo))
            df = fetch_crop_data(combo_dict)
            if not df.empty:
                crop_dfs.append(df)
        crop_df = pd.concat(crop_dfs, ignore_index=True) if crop_dfs else pd.DataFrame()

    # Extract rainfall filters
    rain_prompt = f"""
You are a data analyst working with Indian rainfall data from IMD.

Your task is to extract structured filters from the following user query:
\"{question}\"

Only respond if the query is related to rainfall, climate, or precipitation. Otherwise, return None.

Return a JSON object with exactly these keys:
- subdivision: Match using substring (e.g., "Delhi" should match "East Delhi"). If not specified, set to None (meaning include all subdivisions).
- rainfall_year: If a range like "2019–2021" is mentioned, expand it to a list of years. If no year is mentioned, default to [2014–2017]. If phrases like "last N years", "last year", "recent years", or "decade" are used, interpret them relative to 2017 (e.g., "last 3 years" → [2015, 2016, 2017]).
- rainfall_metric: Choose from [JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC, ANNUAL, JF, MAM, JJAS, OND].

Do not include any explanation or formatting outside the JSON block.
"""
    rain_entities = extract_entities(rain_prompt)
    print("Rainfall Entities:", rain_entities)

    rain_df = pd.DataFrame()
    if rain_entities:
        rain_df = pd.read_csv('./data/rainfall_data.csv')
        subdivisions = rain_entities.get("subdivision")
        years = rain_entities.get("rainfall_year", [])
        if isinstance(subdivisions, str):
            subdivisions = [subdivisions]
        elif subdivisions is None:
            subdivisions = rain_df["SUBDIVISION"].dropna().unique().tolist()

        if isinstance(years, int):
            years = [years]

        filtered_rain_dfs = []
        for sub in subdivisions:
            pattern = re.escape(sub)
            df = rain_df[rain_df["SUBDIVISION"].str.contains(pattern, case=False, na=False)]
            if years:
                df = df[df["YEAR"].isin(years)]
            if not df.empty:
                filtered_rain_dfs.append(df)

        rain_df = pd.concat(filtered_rain_dfs, ignore_index=True) if filtered_rain_dfs else pd.DataFrame()

    # Fallback: if crop_df is empty, use crop-wise-area-production-yield.csv
    if crop_df.empty and crop_entities:
        fallback_df = pd.read_csv('./data/crop-wise-area-production-yield.csv')

# Normalize column names and strip whitespace from all string cells
        fallback_df.columns = fallback_df.columns.str.strip().str.lower()
        for col in fallback_df.select_dtypes(include='object').columns:
            fallback_df[col] = fallback_df[col].str.strip()

        crop_filters = {
            k: v if isinstance(v, list) else [v]
            for k, v in crop_entities.items() if v is not None
        }

        raw_years = interpret_crop_years(crop_entities.get("crop_year", []))
        financial_years = convert_years_to_financial_format(raw_years)
        crop_filters["crop_year"] = financial_years

        keys = list(crop_filters.keys())
        combinations = list(product(*[crop_filters[k] for k in keys]))
        fallback_dfs = []
        print(combinations)
        for combo in combinations:
            combo_dict = dict(zip(keys, combo))
            df = fallback_df.copy()
            if "state_name" in combo_dict:
                df = df[df["state_name"].str.contains(combo_dict["state_name"], case=False, na=False)]
            if "district_name" in combo_dict:
                df = df[df["district_name"].str.contains(combo_dict["district_name"], case=False, na=False)]
            if "season" in combo_dict:
                df = df[df["season"].str.contains(combo_dict["season"], case=False, na=False)]
            if "crop" in combo_dict and combo_dict["crop"]:
                df = df[df["crop_name"].str.contains(combo_dict["crop"], case=False, na=False)]
            if "crop_year" in combo_dict:
                crop_years = combo_dict["crop_year"]
                if isinstance(crop_years, str):
                    crop_years = [crop_years]
                df = df[df["year"].isin(crop_years)]
            if not df.empty:
                fallback_dfs.append(df)

            print(fallback_dfs)

        crop_df = pd.concat(fallback_dfs, ignore_index=True) if fallback_dfs else pd.DataFrame()
        print(crop_df)

    return (gpt_response(question, crop_df, rain_df), crop_df, rain_df)