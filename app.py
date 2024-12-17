import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Function to load data from local CSV files
@st.cache_data
def load_data():
    try:
        chart_events = pd.read_csv("CHARTEVENTS.csv", nrows=5000)
        icu_stays = pd.read_csv("ICUSTAYS.csv")
        d_items = pd.read_csv("D_ITEMS.csv")
        return chart_events, icu_stays, d_items
    except FileNotFoundError as e:
        st.error(f"Error loading files: {e}")
        return None, None, None

# Load data
chart_events, icu_stays, d_items = load_data()
if chart_events is None or icu_stays is None or d_items is None:
    st.stop()

# Debugging: Verify Columns
st.write("Columns in chart_events:", chart_events.columns)
st.write("Columns in icu_stays:", icu_stays.columns)
st.write("Columns in d_items:", d_items.columns)

# Ensure 'subject_id' column exists in icu_stays
if 'subject_id' not in icu_stays.columns:
    st.error("'subject_id' column is missing in ICUSTAYS.csv. Please check the file.")
    st.stop()

# Data Merging
chart_events = chart_events.dropna(subset=["itemid", "valuenum"])
merged_data = pd.merge(chart_events, icu_stays[['icustay_id', 'subject_id', 'los', 'first_careunit']], 
                       on="icustay_id", how="inner")
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on="itemid", how="inner")

st.write("Columns in merged_data:", merged_data.columns)  # Debugging merged_data columns

# Sidebar Filters
st.sidebar.title("Filters")
care_unit_filter = st.sidebar.multiselect(
    "Select Care Units", 
    icu_stays["first_careunit"].unique(), 
    default=icu_stays["first_careunit"].unique()
)

# Filtered Data
filtered_data = merged_data[merged_data["first_careunit"].isin(care_unit_filter)]

# Main Dashboard Title
st.title("ICU Management Dashboard")

# Metrics
st.subheader("Key Metrics")
total_patients = filtered_data["subject_id"].nunique()
average_los = filtered_data["los"].mean()

col1, col2 = st.columns(2)
col1.metric("Total Patients", total_patients)
col2.metric("Average Length of Stay (LOS)", f"{average_los:.2f} days")

# Visualizations
st.subheader("ICU Care Unit Distribution")
care_unit_dist = icu_stays["first_careunit"].value_counts().reset_index()
care_unit_dist.columns = ["Care Unit", "Count"]
fig_pie = px.pie(care_unit_dist, names="Care Unit", values="Count", title="ICU Care Unit Distribution")
st.plotly_chart(fig_pie)

# Filtered Data Preview
st.subheader("Filtered Data Preview")
st.dataframe(filtered_data.head())
