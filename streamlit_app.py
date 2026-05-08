import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import json
from io import BytesIO
import requests
import numpy as np

st.set_page_config(page_title="AI BI Studio", page_icon="📊", layout="wide")

st.title("📊 AI BI Studio")
st.subheader("Intelligent Power BI Alternative with Groq AI")
st.caption("By Mohammed Amine Goumri | Real LLM-Powered BI")

# Sidebar
with st.sidebar:
    st.header("🔑 Groq API Configuration")
    groq_key = st.text_input("Groq API Key", type="password", help="Get free key at console.groq.com")
    if groq_key:
        st.session_state.groq_key = groq_key
        st.success("✅ Connected to Groq")
    st.divider()
    page = st.radio("Navigation", [
        "🏠 Home",
        "📤 Upload Data",
        "🧹 AI Data Cleaner",
        "📊 Smart Visualizations",
        "💡 Natural Language Insights",
        "🏗️ Dashboard Builder"
    ])

client = None
if "groq_key" in st.session_state:
    client = Groq(api_key=st.session_state.groq_key)

def ask_groq(prompt, model="llama-3.1-70b-versatile"):
    if not client:
        return "Please enter your Groq API key in the sidebar."
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Groq Error: {str(e)}"

# Data loading function
@st.cache_data
def load_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type")
        return None

if page == "🏠 Home":
    st.markdown("""
    ### Welcome to AI BI Studio!
    
    **Upload any dataset → Let AI clean and understand it → Ask questions in plain English → Build professional dashboards instantly.**
    
    Powered by Groq's lightning-fast Llama 3.1 70B.
    """)
    st.balloons()

elif page == "📤 Upload Data":
    st.header("📤 Upload Your Data")
    col1, col2 = st.columns([3,2])
    with col1:
        uploaded = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx', 'xls'])
    with col2:
        api_url = st.text_input("Or load from API (JSON)", placeholder="https://api.example.com/data")
    
    if uploaded:
        df = load_file(uploaded)
        if df is not None:
            st.success(f"✅ Loaded {df.shape[0]:,} rows and {df.shape[1]} columns")
            st.dataframe(df.head(10), use_container_width=True)
            st.session_state['df'] = df
    
    if api_url and st.button("Load from API"):
        try:
            r = requests.get(api_url)
            data = r.json()
            df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame(data)
            st.session_state['df'] = df
            st.success("✅ Data loaded from API")
        except Exception as e:
            st.error(f"API Error: {e}")

elif page == "🧹 AI Data Cleaner":
    if 'df' not in st.session_state:
        st.warning("Please upload data first")
    else:
        st.header("🧹 AI-Powered Data Cleaning")
        df = st.session_state['df'].copy()
        
        st.subheader("Current Data Overview")
        st.write(f"**Shape:** {df.shape}")
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes,
            'Missing': df.isnull().sum().values,
            '% Missing': (df.isnull().sum() / len(df) * 100).round(2).values
        })
        st.dataframe(col_info, use_container_width=True)
        
        if st.button("🚀 Let AI Analyze & Clean Data", type="primary"):
            with st.spinner("Groq AI is analyzing your dataset..."):
                context = f"""
                Dataset shape: {df.shape}
                Columns: {list(df.columns)}
                Data types: {df.dtypes.to_dict()}
                Missing values per column: {df.isnull().sum().to_dict()}
                Sample data:
                {df.head(6).to_string()}
                """
                prompt = f"""You are an expert Data Engineer. Analyze the following dataset and write clean, efficient pandas code to improve data quality.
                - Fix data types
                - Handle missing values intelligently
                - Remove duplicates if any
                - Standardize column names if needed
                - Any other obvious improvements

                Return **only** the pandas code (no explanations). The code should modify 'df' in place and end with the cleaned dataframe.

                Dataset info:
                {context}"""
                
                code = ask_groq(prompt)
                st.code(code, language="python")
                
                if st.button("✅ Apply AI Cleaning Code"):
                    try:
                        local_vars = {'df': df}
                        exec(code, {"pd": pd, "np": np}, local_vars)
                        cleaned_df = local_vars.get('df', df)
                        st.session_state['df'] = cleaned_df
                        st.success("🎉 AI Cleaning applied successfully!")
                        st.dataframe(cleaned_df.head())
                    except Exception as e:
                        st.error(f"Error applying code: {e}")

elif page == "📊 Smart Visualizations":
    if 'df' not in st.session_state:
        st.warning("Upload data first")
    else:
        df = st.session_state['df']
        st.header("📊 Smart Visualizations")
        
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        st.write("**Detected numeric columns:**", num_cols)
        st.write("**Detected categorical columns:**", cat_cols)
        
        chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Box Plot"])
        
        if chart_type == "Bar Chart" and cat_cols and num_cols:
            x = st.selectbox("X Axis (Category)", cat_cols)
            y = st.selectbox("Y Axis (Numeric)", num_cols)
            fig = px.bar(df, x=x, y=y)
            st.plotly_chart(fig, use_container_width=True)
        # Add more chart types...

st.caption("🔥 AI BI Studio v2 • Powered by Groq Llama 3.1")
