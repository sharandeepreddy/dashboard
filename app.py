import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load datasets
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

# Merge datasets
chart_events = chart_events.dropna(subset=["itemid", "valuenum"])  # Remove null measurements
merged_data = pd.merge(chart_events, icu_stays[['icustay_id', 'subject_id', 'los', 'first_careunit']], 
                       on="icustay_id", how="inner")
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on="itemid", how="inner")

# Sidebar Filters
st.sidebar.title("Filters")
care_unit_filter = st.sidebar.multiselect("Select Care Units", icu_stays["first_careunit"].unique(), 
                                          default=icu_stays["first_careunit"].unique())

# Filter Data
filtered_data = merged_data[merged_data["first_careunit"].isin(care_unit_filter)]

# Main Dashboard Title
st.title("ICU Management Dashboard")

# Metrics
st.subheader("Key Metrics")
total_patients = icu_stays["subject_id"].nunique()
average_los = icu_stays["los"].mean()

col1, col2 = st.columns(2)
col1.metric("Total Patients", total_patients)
col2.metric("Average Length of Stay (LOS)", f"{average_los:.2f} days")

# Pie Chart: ICU Care Unit Distribution
st.subheader("ICU Care Unit Distribution")
care_unit_dist = icu_stays["first_careunit"].value_counts().reset_index()
care_unit_dist.columns = ["Care Unit", "Count"]
fig_pie = px.pie(care_unit_dist, names="Care Unit", values="Count", title="ICU Care Unit Distribution")
st.plotly_chart(fig_pie)

# Bar Chart: Top Measurements
st.subheader("Top 10 Measurements Collected")
top_measurements = filtered_data["label"].value_counts().nlargest(10).reset_index()
top_measurements.columns = ["Measurement", "Count"]
fig_bar = px.bar(top_measurements, x="Measurement", y="Count", title="Top 10 Measurements Collected")
st.plotly_chart(fig_bar)

# Scatter Plot: LOS vs. Measurement Value
st.subheader("Length of Stay vs. Measurement Value")
fig_scatter = px.scatter(filtered_data, x="los", y="valuenum", color="label",
                         title="Length of Stay vs Measurement Value",
                         labels={"los": "Length of Stay (days)", "valuenum": "Measurement Value"})
st.plotly_chart(fig_scatter)

# Table: ICU Care Unit Summary
st.subheader("ICU Care Unit Summary")
icu_summary = icu_stays.groupby("first_careunit").agg(
    Total_Stays=("icustay_id", "count"),
    Avg_LOS=("los", "mean")
).reset_index()
st.dataframe(icu_summary)
