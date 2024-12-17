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

# Merge datasets (ensure 'subject_id' is retained)
chart_events = chart_events.dropna(subset=["itemid", "valuenum"])
merged_data = pd.merge(
    chart_events[['icustay_id', 'itemid', 'valuenum']],
    icu_stays[['icustay_id', 'subject_id', 'los', 'first_careunit', 'intime']],
    on="icustay_id", how="inner"
)
merged_data = pd.merge(
    merged_data, 
    d_items[['itemid', 'label']], 
    on="itemid", how="inner"
)

# Convert `intime` to datetime for filtering
merged_data["intime"] = pd.to_datetime(merged_data["intime"], errors='coerce')

# Sidebar Filters
st.sidebar.title("Filters")

# ICU Care Unit Filter
care_unit_filter = st.sidebar.multiselect(
    "Select Care Units", 
    icu_stays["first_careunit"].unique(), 
    default=icu_stays["first_careunit"].unique()
)

# Measurement Filter
measurement_filter = st.sidebar.multiselect(
    "Select Measurement Types", 
    merged_data["label"].unique(), 
    default=merged_data["label"].unique()[:5]
)

# LOS Range Slider
los_range = st.sidebar.slider(
    "Select LOS Range", 
    int(merged_data["los"].min()), 
    int(merged_data["los"].max()), 
    (0, 10)
)

# Date Range Picker
start_date, end_date = st.sidebar.date_input(
    "Select Admission Date Range", 
    [merged_data["intime"].min(), merged_data["intime"].max()]
)

# Filter Data
filtered_data = merged_data[
    (merged_data["first_careunit"].isin(care_unit_filter)) &
    (merged_data["label"].isin(measurement_filter)) &
    (merged_data["los"].between(los_range[0], los_range[1])) &
    (merged_data["intime"].between(pd.Timestamp(start_date), pd.Timestamp(end_date)))
]

# Debugging: Check Columns and Data
st.write("Filtered Data Columns:", filtered_data.columns)
st.write("Filtered Data Preview:", filtered_data.head())

# Key Metrics (with Safe Checks)
st.subheader("Key Metrics")
if "subject_id" in filtered_data.columns:
    total_patients = filtered_data["subject_id"].nunique()
else:
    st.warning("The column 'subject_id' is missing from the filtered data.")
    total_patients = 0

average_los = filtered_data["los"].mean() if "los" in filtered_data.columns else 0
unique_measurements = filtered_data["label"].nunique() if "label" in filtered_data.columns else 0

col1, col2, col3 = st.columns(3)
col1.metric("Filtered Total Patients", total_patients)
col2.metric("Average LOS (days)", f"{average_los:.2f}")
col3.metric("Unique Measurements", unique_measurements)

# Pie Chart: ICU Care Unit Distribution
st.subheader("ICU Care Unit Distribution")
if "first_careunit" in filtered_data.columns:
    care_unit_dist = filtered_data["first_careunit"].value_counts().reset_index()
    care_unit_dist.columns = ["Care Unit", "Count"]
    fig_pie = px.pie(care_unit_dist, names="Care Unit", values="Count", title="Care Unit Distribution")
    st.plotly_chart(fig_pie)
else:
    st.warning("No 'first_careunit' data available to plot.")

# Bar Chart: Top Measurements
st.subheader("Top 10 Measurements Collected")
if "label" in filtered_data.columns:
    top_measurements = filtered_data["label"].value_counts().nlargest(10).reset_index()
    top_measurements.columns = ["Measurement", "Count"]
    fig_bar = px.bar(top_measurements, x="Measurement", y="Count", title="Top 10 Measurements Collected")
    st.plotly_chart(fig_bar)
else:
    st.warning("No 'label' data available to plot.")

# Scatter Plot: LOS vs Measurement Value
st.subheader("Length of Stay vs Measurement Value")
if "los" in filtered_data.columns and "valuenum" in filtered_data.columns:
    fig_scatter = px.scatter(
        filtered_data, x="los", y="valuenum", color="label",
        title="Length of Stay vs Measurement Value",
        labels={"los": "Length of Stay (days)", "valuenum": "Measurement Value"}
    )
    st.plotly_chart(fig_scatter)
else:
    st.warning("Insufficient data to plot LOS vs Measurement Value.")

# Table: ICU Care Unit Summary
st.subheader("ICU Care Unit Summary")
if "first_careunit" in filtered_data.columns:
    icu_summary = filtered_data.groupby("first_careunit").agg(
        Total_Stays=("icustay_id", "count"),
        Avg_LOS=("los", "mean")
    ).reset_index()
    st.dataframe(icu_summary)
else:
    st.warning("No 'first_careunit' data available to summarize.")

# Filtered Data Preview
st.write("### Filtered Data Preview")
st.dataframe(filtered_data.head())
