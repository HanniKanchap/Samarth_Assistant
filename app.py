import streamlit as st
from answer_generator import generate_answer
import pandas as pd

st.set_page_config(page_title="Project Samarth Q&A", layout="centered")
st.title("🌾 Project Samarth Q&A System")
st.markdown("Ask a question about **agriculture** or **climate** and get a data-backed answer:")

question = st.text_input("Your question:")

if st.button("Get Answer"):
    with st.spinner("🔍 Analyzing and fetching data..."):
        answer = generate_answer(question)

        # Display formatted response
        st.markdown("### ✅ Answer")
        if isinstance(answer, tuple) and len(answer) == 3:
            response_text, crop_df, rain_df = answer
            st.markdown(response_text, unsafe_allow_html=True)

            if not crop_df.empty or not rain_df.empty:
                with st.expander("📊 View Data Used"):
                    if not crop_df.empty:
                        st.subheader("🌱 Crop Data")
                        st.dataframe(crop_df)
                    if not rain_df.empty:
                        st.subheader("🌧️ Rainfall Data")
                        st.dataframe(rain_df)
        else:
            st.markdown(answer, unsafe_allow_html=True)