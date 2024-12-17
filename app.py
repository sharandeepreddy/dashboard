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
        st.error(f"File not found: {e}")
        return None, None, None

# Load Data
chart_events, icu_stays, d_items = load_data()
if chart_events is None or icu_stays is None or d_items is None:
    st.stop()

# Merge Data
merged_data = pd.merge(chart_events, icu_stays[['icustay_id', 'subject_id', 'first_careunit', 'los']], on='icustay_id')
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on='itemid')

# Metrics
st.title("ICU Management Dashboard")
st.subheader("Key Metrics")

total_patients = icu_stays["subject_id"].nunique()
avg_los = icu_stays["los"].mean()

col1, col2 = st.columns(2)
col1.metric("Total Patients", total_patients)
col2.metric("Average Length of Stay (LOS)", f"{avg_los:.2f} days")

# Pie Chart: ICU Care Unit Distribution
st.subheader("ICU Care Unit Distribution")
care_unit_dist = icu_stays["first_careunit"].value_counts().reset_index()
care_unit_dist.columns = ["Care Unit", "Count"]
fig_care_unit = px.pie(care_unit_dist, names="Care Unit", values="Count", title="Care Unit Distribution")
st.plotly_chart(fig_care_unit)

# Donut Chart: Patient Status
st.subheader("Tasks by Status")
status_counts = merged_data["label"].value_counts().reset_index()
status_counts.columns = ["Measurement Type", "Count"]
fig_status = px.pie(status_counts, names="Measurement Type", values="Count", hole=0.5, title="Measurements Collected")
st.plotly_chart(fig_status)

# Gauge Chart: Total Utilized Work Hours
st.subheader("Total Utilized ICU Hours")
total_utilized_hours = icu_stays["los"].sum()
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=total_utilized_hours,
    title={"text": "Total ICU Hours"},
    domain={'x': [0, 1], 'y': [0, 1]},
    gauge={'axis': {'range': [0, 50000]},
           'steps': [{'range': [0, total_utilized_hours * 0.7], 'color': "lightgray"},
                     {'range': [total_utilized_hours * 0.7, total_utilized_hours], 'color': "gray"}],
           'bar': {'color': "darkblue"}}
))
st.plotly_chart(fig_gauge)

# Scatter Plot: Length of Stay vs. Measurement Value
st.subheader("Length of Stay vs. Measurement Value")
scatter_data = merged_data.dropna(subset=["los", "valuenum"])
fig_scatter = px.scatter(scatter_data, x="los", y="valuenum", color="label",
                         title="LOS vs Measurement Value",
                         labels={"los": "Length of Stay (days)", "valuenum": "Measurement Value"})
st.plotly_chart(fig_scatter)

# Task Summary Table
st.subheader("Patient Summary by ICU Stay")
summary_table = icu_stays.groupby("first_careunit").agg(
    Total_Stays=("icustay_id", "count"),
    Avg_LOS=("los", "mean")
).reset_index()
st.dataframe(summary_table)
