import json
from groq import Groq
import streamlit as st

groq_api_key = st.secrets["GROQ_API_KEY"]
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found")

client = Groq(api_key=groq_api_key)

def extract_entities(prompt):
    prompt = prompt

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )

    try:
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        print("Failed to parse JSON from model response:")
        print(completion.choices[0].message.content)
        return {}

def gpt_response(question, crop_data, rain_data):
    # Build dataset descriptions conditionally
    crop_text = ""
    rain_text = ""

    if not crop_data.empty:
        crop_text = f"""1. Crop Data (CSV format):
{crop_data.tail(100).to_string(index=False)}"""

    if not rain_data.empty:
        rain_text = f"""2. Rainfall Data (CSV format):
{rain_data.tail(100).to_string(index=False)}"""

    # Compose the prompt dynamically
    prompt = f"""
You are a government data analyst working with agricultural and climate datasets.

Here is the user's question:
\"{question}\"

You are provided with the following dataset(s):
{crop_text if crop_text else ""}
{rain_text if rain_text else ""}

Your task:
- Interpret the question.
- Analyze the available data.
- Generate a clear, concise, and data-backed answer.
- Include specific numbers and trends if relevant.
- Mention which dataset(s) you used.

Only return the answer. Do not explain your reasoning or include any extra formatting.
"""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_completion_tokens=2048,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )

    return completion.choices[0].message.content