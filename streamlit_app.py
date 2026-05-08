import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import json
from io import BytesIO
import requests
import numpy as np
from datetime import datetime

st.set_page_config(page_title="AI BI Studio", page_icon="📊", layout="wide")

st.title("📊 AI BI Studio")
st.subheader("Your Intelligent Power BI Alternative")
st.caption("By Mohammed Amine Goumri • Powered by Groq Llama 3.1 70B")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔑 Groq LLM")
    groq_key = st.text_input("Groq API Key", type="password", value=st.session_state.get("groq_key", ""), help="Get free key at https://console.groq.com/keys")
    if groq_key:
        st.session_state.groq_key = groq_key
        st.success("✅ Groq Connected")
    else:
        st.warning("Enter Groq API key to unlock AI features")
    
    st.divider()
    st.header("Navigation")
    page = st.radio("Go to", [
        "🏠 Home",
        "📤 Upload Data",
        "🧹 AI Data Cleaner",
        "📊 Smart Visualizations",
        "💡 Natural Language BI",
        "🏗️ Dashboard Builder"
    ])

# ====================== GROQ CLIENT ======================
@st.cache_resource
def get_client():
    if "groq_key" in st.session_state and st.session_state.groq_key:
        return Groq(api_key=st.session_state.groq_key)
    return None

client = get_client()

def ask_groq(prompt, model="llama-3.1-70b-versatile", temperature=0.2):
    if not client:
        return "Please add your Groq API key in the sidebar."
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Groq API Error: {str(e)}"

# ====================== DATA LOADING ======================
@st.cache_data
def load_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format")
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

if 'df' not in st.session_state:
    st.session_state.df = None

# ====================== PAGES ======================
if page == "🏠 Home":
    st.success("🚀 Welcome to the future of Business Intelligence!")
    st.markdown("""
    ### What you can do:
    - Upload Excel / CSV / API data
    - Let **AI** intelligently clean and prepare your data
    - Ask questions in plain English ("Show me sales by region in 2025")
    - Get automatic chart recommendations
    - Build professional dashboards
    """)
    st.balloons()

elif page == "📤 Upload Data":
    st.header("📤 Upload Your Dataset")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx', 'xls'])
    with col2:
        api_url = st.text_input("Or load from Live API (JSON)", placeholder="https://api.example.com/data")
    
    if uploaded_file is not None:
        df = load_file(uploaded_file)
        if df is not None:
            st.success(f"✅ Successfully loaded **{df.shape[0]:,} rows** and **{df.shape[1]} columns**")
            st.dataframe(df.head(), use_container_width=True)
            st.session_state.df = df
    
    if api_url and st.button("Load from API"):
        try:
            resp = requests.get(api_url)
            data = resp.json()
            if isinstance(data, list):
                df = pd.json_normalize(data)
            else:
                df = pd.DataFrame(data)
            st.session_state.df = df
            st.success("✅ Data loaded from API!")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load API: {e}")

elif page == "🧹 AI Data Cleaner":
    if st.session_state.df is None:
        st.warning("Please upload data first on the Upload page.")
    else:
        st.header("🧹 AI Data Cleaner")
        df = st.session_state.df.copy()
        
        st.subheader("Data Quality Overview")
        info = pd.DataFrame({
            "Column": df.columns,
            "Dtype": df.dtypes,
            "Non-Null": df.count().values,
            "Missing %": ((df.isnull().sum() / len(df)) * 100).round(2)
        })
        st.dataframe(info, use_container_width=True)
        
        if st.button("🚀 Let Groq AI Clean This Data", type="primary"):
            with st.spinner("AI is analyzing structure and cleaning data..."):
                context = f"""
                Shape: {df.shape}
                Columns: {list(df.columns)}
                Data types: {df.dtypes.to_dict()}
                Missing values: {df.isnull().sum().to_dict()}
                Sample:\n{df.head(5).to_string()}
                """
                prompt = f"""You are a world-class data engineer.
                Write clean pandas code to intelligently clean this dataset.
                Rules:
                - Fix incorrect data types
                - Handle missing values smartly
                - Remove exact duplicate rows
                - Standardize column names (lowercase + underscore)
                - Any other quality improvements

                Return **only** executable pandas code. Do not include explanations.
                Dataset context:
                {context}"""
                
                code = ask_groq(prompt)
                st.code(code, language="python")
                
                if st.button("Apply this AI Cleaning Code"):
                    try:
                        local = {"df": df, "pd": pd, "np": np}
                        exec(code, {"pd": pd, "np": np}, local)
                        cleaned = local.get("df", df)
                        st.session_state.df = cleaned
                        st.success("🎉 Data cleaned by AI successfully!")
                        st.dataframe(cleaned.head())
                    except Exception as e:
                        st.error(f"Execution error: {e}")

elif page == "💡 Natural Language BI":
    if st.session_state.df is None:
        st.warning("Upload data first")
    else:
        st.header("💡 Ask AI Anything")
        question = st.text_input("Ask a business question or request a new column:", 
                               placeholder="What is the total sales by region in 2025? or Create profit margin column")
        
        if st.button("Get Answer & Code", type="primary"):
            with st.spinner("Groq is analyzing your data..."):
                df = st.session_state.df
                prompt = f"""You are a Senior BI Analyst.
                Dataset columns: {list(df.columns)}
                Sample data:\n{df.head(6).to_string()}

                User request: {question}

                Provide:
                1. Pandas code to compute the answer or create the new column
                2. A short business insight
                """
                response = ask_groq(prompt, temperature=0.3)
                st.markdown(response)

elif page == "📊 Smart Visualizations":
    if st.session_state.df is None:
        st.warning("Upload data first")
    else:
        df = st.session_state.df
        st.header("📊 Smart Visualizations")
        
        if st.button("Get AI Chart Recommendations"):
            prompt = f"Suggest the 6 best visualizations for this dataset. Columns: {list(df.columns)}"
            recs = ask_groq(prompt)
            st.write(recs)
        
        # Quick charts
        st.subheader("Quick Charts")
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            if cat_cols and num_cols:
                x = st.selectbox("X Axis", cat_cols, key="x_axis")
                y = st.selectbox("Y Axis", num_cols, key="y_axis")
                if st.button("Create Bar Chart"):
                    fig = px.bar(df, x=x, y=y, title=f"{y} by {x}")
                    st.plotly_chart(fig, use_container_width=True)
        with col2:
            if len(num_cols) >= 2:
                x = st.selectbox("X Axis (Scatter)", num_cols, key="scatter_x")
                y = st.selectbox("Y Axis (Scatter)", num_cols, key="scatter_y")
                if st.button("Create Scatter Plot"):
                    fig = px.scatter(df, x=x, y=y, title=f"{x} vs {y}")
                    st.plotly_chart(fig, use_container_width=True)

elif page == "🏗️ Dashboard Builder":
    st.header("🏗️ Dashboard Builder (Coming Soon)")
    st.info("This section will allow you to build full interactive dashboards with titles, KPIs, and saved layouts.")
    st.write("The foundation is ready — we can expand this powerfully next.")

st.caption("🔥 AI BI Studio • Real LLM-Powered Business Intelligence • v2.0")
