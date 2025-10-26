import pandas as pd
import requests
from io import StringIO
import streamlit as st

key = st.secrets['DATA_API_KEY']
def fetch_rainfall_data(api_key="579b464db66ec23bdd000001c082134a1113493a7b97920f84757672"):
    url = f"https://api.data.gov.in/resource/8e0bd482-4aba-4d99-9cb9-ff124f6f1c2f?api-key={api_key}&format=csv&limit=5000"
    response = requests.get(url)
    df = pd.read_csv(StringIO(response.text))
    print(df)
    return df

if __name__ == '__main__':
    df = fetch_rainfall_data()
    df.to_csv('./data/rainfall_data.csv')
    print(df)
