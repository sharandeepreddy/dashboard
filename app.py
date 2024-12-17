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
merged_data = pd.merge(chart_events, icu_stays[['icustay_id', 'subject_id', 'los', 'first_careunit', 'intime']], on="icustay_id", how="inner")
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on="itemid", how="inner")

# Convert `intime` to datetime for date filtering
merged_data["intime"] = pd.to_datetime(merged_data["intime"], errors='coerce')

# Sidebar Filters
st.sidebar.title("Filters")

# ICU Care Unit Filter
care_unit_filter = st.sidebar.multiselect("Select Care Units", 
                                          icu_stays["first_careunit"].unique(),
                                          default=icu_stays["first_careunit"].unique())

# Measurement Filter
measurement_filter = st.sidebar.multiselect("Select Measurement Types", 
                                            merged_data["label"].unique(),
                                            default=merged_data["label"].unique()[:5])

# LOS Range Slider
los_range = st.sidebar.slider("Select LOS Range", 
                              int(merged_data["los"].min()), 
                              int(merged_data["los"].max()), 
                              (0, 10))

# Date Range Picker
start_date, end_date = st.sidebar.date_input("Select Admission Date Range", 
                                             [merged_data["intime"].min(), merged_data["intime"].max()])

# Filter Data
filtered_data = merged_data[
    (merged_data["first_careunit"].isin(care_unit_filter)) &
    (merged_data["label"].isin(measurement_filter)) &
    (merged_data["los"].between(los_range[0], los_range[1])) &
    (merged_data["intime"].between(pd.Timestamp(start_date), pd.Timestamp(end_date)))
]

# Main Dashboard Title
st.title("ICU Management Dashboard")

# Key Metrics (Dynamic)
st.subheader("Key Metrics")
total_patients = filtered_data["subject_id"].nunique()
average_los = filtered_data["los"].mean()
unique_measurements = filtered_data["label"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Filtered Total Patients", total_patients)
col2.metric("Average LOS (days)", f"{average_los:.2f}")
col3.metric("Unique Measurements", unique_measurements)

# Pie Chart: ICU Care Unit Distribution
st.subheader("ICU Care Unit Distribution")
care_unit_dist = filtered_data["first_careunit"].value_counts().reset_index()
care_unit_dist.columns = ["Care Unit", "Count"]
fig_pie = px.pie(care_unit_dist, names="Care Unit", values="Count", title="Care Unit Distribution")
st.plotly_chart(fig_pie)

# Bar Chart: Top 10 Measurements
st.subheader("Top 10 Measurements Collected")
top_measurements = filtered_data["label"].value_counts().nlargest(10).reset_index()
top_measurements.columns = ["Measurement", "Count"]
fig_bar = px.bar(top_measurements, x="Measurement", y="Count", title="Top 10 Measurements Collected")
st.plotly_chart(fig_bar)

# Scatter Plot: LOS vs Measurement Value
st.subheader("Length of Stay vs Measurement Value")
fig_scatter = px.scatter(filtered_data, x="los", y="valuenum", color="label",
                         title="Length of Stay vs Measurement Value",
                         labels={"los": "Length of Stay (days)", "valuenum": "Measurement Value"})
st.plotly_chart(fig_scatter)

# Histogram: Distribution of LOS
st.subheader("Distribution of Length of Stay")
fig_hist = px.histogram(filtered_data, x="los", nbins=30, title="Distribution of Length of Stay")
st.plotly_chart(fig_hist)

# Line Chart: Trend of Measurements Over Time
st.subheader("Measurement Trends Over Time")
fig_line = px.line(filtered_data, x="intime", y="valuenum", color="label", 
                   title="Measurement Trends Over Time",
                   labels={"intime": "Admission Date", "valuenum": "Measurement Value"})
st.plotly_chart(fig_line)

# Table: ICU Summary
st.subheader("ICU Care Unit Summary")
icu_summary = filtered_data.groupby("first_careunit").agg(
    Total_Stays=("icustay_id", "count"),
    Avg_LOS=("los", "mean")
).reset_index()
st.dataframe(icu_summary)

# Filtered Data Preview
st.write("### Filtered Data Preview")
st.dataframe(filtered_data.head())
