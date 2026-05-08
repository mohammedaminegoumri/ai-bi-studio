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
import plotly.io as pio

st.set_page_config(page_title="AI BI Studio", page_icon="📊", layout="wide")

st.title("📊 AI BI Studio")
st.subheader("Your Intelligent Power BI Alternative")
st.caption("By Mohammed Amine Goumri • Powered by Groq Llama 3.1")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔑 Groq LLM")
    groq_key = st.text_input("Groq API Key", type="password", value=st.session_state.get("groq_key", ""), help="Get free key at https://console.groq.com/keys")
    if groq_key:
        st.session_state.groq_key = groq_key
        st.success("✅ Groq Connected")
    else:
        st.warning("Enter Groq API key to unlock full AI power")
    
    st.divider()
    st.header("Navigation")
    page = st.radio("Go to", [
        "🏠 Home",
        "📤 Upload Data",
        "🧹 AI Data Cleaner",
        "💡 Natural Language BI",
        "📊 Smart Visualizations",
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
            max_tokens=2500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Groq API Error: {str(e)}"

# ====================== SESSION STATE ======================
if 'df' not in st.session_state:
    st.session_state.df = None
if 'dashboard_elements' not in st.session_state:
    st.session_state.dashboard_elements = []  # Store KPIs and charts

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

# ====================== PAGES ======================
if page == "🏠 Home":
    st.success("🚀 Welcome to AI BI Studio - Your Smart Power BI")
    st.markdown("""
    ### Key Features:
    - AI-powered data cleaning
    - Natural language questions & calculated columns
    - Smart visualizations
    - Professional KPI cards
    - Full dashboard builder with export
    """)
    st.balloons()

elif page == "📤 Upload Data":
    # (keep similar to before)
    st.header("📤 Upload Your Dataset")
    col1, col2 = st.columns([3, 2])
    with col1:
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx', 'xls'])
    with col2:
        api_url = st.text_input("Or load from Live API (JSON)", placeholder="https://api.example.com/data")
    
    if uploaded_file is not None:
        df = load_file(uploaded_file)
        if df is not None:
            st.success(f"✅ Loaded **{df.shape[0]:,} rows** × **{df.shape[1]} columns**")
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
        st.warning("Please upload data first")
    else:
        st.header("🧹 AI Data Cleaner")
        df = st.session_state.df.copy()
        
        st.subheader("Data Quality")
        info = pd.DataFrame({
            "Column": df.columns,
            "Dtype": df.dtypes,
            "Non-Null": df.count().values,
            "Missing %": ((df.isnull().sum() / len(df)) * 100).round(2)
        })
        st.dataframe(info, use_container_width=True)
        
        if st.button("🚀 Let Groq AI Clean This Data", type="primary"):
            with st.spinner("AI is cleaning your data..."):
                context = f"""
                Shape: {df.shape}
                Columns: {list(df.columns)}
                Data types: {df.dtypes.to_dict()}
                Missing values: {df.isnull().sum().to_dict()}
                Sample:\n{df.head(5).to_string()}
                """
                prompt = f"""You are a world-class data engineer.
Write clean pandas code to intelligently clean this dataset.
Include handling for data types, missing values, duplicates, and column name standardization.
Return ONLY the executable pandas code for 'df'.
Dataset: {context}"""
                code = ask_groq(prompt)
                st.code(code, language="python")
                
                if st.button("✅ Apply AI Cleaning"):
                    try:
                        local_dict = {"df": df, "pd": pd, "np": np}
                        exec(code, {"pd": pd, "np": np}, local_dict)
                        st.session_state.df = local_dict["df"]
                        st.success("🎉 Data successfully cleaned by AI!")
                    except Exception as e:
                        st.error(f"Error executing code: {e}")

elif page == "💡 Natural Language BI":
    if st.session_state.df is None:
        st.warning("Upload data first")
    else:
        st.header("💡 Natural Language BI")
        question = st.text_input("Ask anything or create new calculated column", 
                               placeholder="Create 'Profit Margin' = (Revenue - Cost) / Revenue * 100")
        
        if st.button("🚀 Get AI Response", type="primary"):
            with st.spinner("Thinking..."):
                df = st.session_state.df
                prompt = f"""You are a Senior BI Analyst.
Dataset columns: {list(df.columns)}
Sample:
{df.head(7).to_string()}

User request: {question}

Respond with:
1. Clear explanation
2. Pandas code to create the new column or compute the metric
"""
                response = ask_groq(prompt, temperature=0.25)
                st.markdown(response)

elif page == "📊 Smart Visualizations":
    if st.session_state.df is None:
        st.warning("Upload data first")
    else:
        st.header("📊 Smart Visualizations")
        df = st.session_state.df
        
        if st.button("Get AI Chart Recommendations"):
            prompt = f"Suggest the best 5 charts for this dataset. Columns: {list(df.columns)}"
            recs = ask_groq(prompt)
            st.write(recs)
        
        # Quick chart builder
        st.subheader("Quick Chart Builder")
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"])
        # ... (add more quick charts)

elif page == "🏗️ Dashboard Builder":
    st.header("🏗️ Dashboard Builder")
    df = st.session_state.df
    
    tab1, tab2, tab3 = st.tabs(["KPI Cards", "Add Charts", "Preview & Export"])
    
    with tab1:
        st.subheader("Add KPI Cards")
        col = st.selectbox("Select Column", df.columns)
        agg = st.selectbox("Aggregation", ["Sum", "Mean", "Count", "Max", "Min"])
        kpi_name = st.text_input("KPI Title", f"Total {col}")
        
        if st.button("Add KPI Card"):
            st.session_state.dashboard_elements.append({
                "type": "kpi",
                "title": kpi_name,
                "column": col,
                "agg": agg
            })
            st.success("KPI added!")
    
    with tab2:
        st.subheader("Add Charts to Dashboard")
        # Simple chart adder
        st.info("Chart adding coming in next upgrade")
    
    with tab3:
        st.subheader("Dashboard Preview")
        cols = st.columns(3)
        for i, elem in enumerate(st.session_state.dashboard_elements):
            with cols[i % 3]:
                if elem["type"] == "kpi":
                    value = df[elem["column"]].agg(elem["agg"].lower())
                    st.metric(label=elem["title"], value=round(value, 2) if isinstance(value, (int, float)) else value)
        
        # Export buttons
        if st.button("Export Dashboard as HTML"):
            html = st.get_html()  # placeholder
            st.download_button("Download HTML", html, "dashboard.html")
        
        st.info("More export options (PNG, PDF) coming soon")

st.caption("🔥 AI BI Studio v3.0 • LLM-Powered • Built for portfolio & real use")
