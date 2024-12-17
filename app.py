import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

# Load datasets
@st.cache_data
def load_data():
    try:
        chart_events = pd.read_csv("CHARTEVENTS.csv", nrows=5000)  # Load sample data
        icu_stays = pd.read_csv("ICUSTAYS.csv")
        d_items = pd.read_csv("D_ITEMS.csv")
        return chart_events, icu_stays, d_items
    except FileNotFoundError as e:
        st.error(f"Error loading files: {e}")
        return None, None, None

# Load the data
chart_events, icu_stays, d_items = load_data()
if chart_events is None or icu_stays is None or d_items is None:
    st.stop()

# Merge datasets
chart_events = chart_events.dropna(subset=["itemid", "valuenum"])  # Drop rows with null measurements
merged_data = pd.merge(chart_events, icu_stays[['icustay_id', 'subject_id', 'los', 'first_careunit', 'intime']], 
                       on="icustay_id", how="inner")
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on="itemid", how="inner")

# Sidebar Filters
st.sidebar.title("Filters")

# ICU Care Unit Multiselect
care_unit_filter = st.sidebar.multiselect("Select Care Units", 
                                          icu_stays["first_careunit"].unique(),
                                          default=icu_stays["first_careunit"].unique())

# Measurements Multiselect with Safe Defaults
available_measurements = merged_data["label"].unique()
default_measurements = available_measurements[:2] if len(available_measurements) > 1 else available_measurements

measurement_filter = st.sidebar.multiselect("Select Measurements", 
                                            available_measurements, 
                                            default=default_measurements)

# Slider for Length of Stay (LOS) Range
los_range = st.sidebar.slider("Select Length of Stay (LOS) Range", 
                              int(icu_stays["los"].min()), int(icu_stays["los"].max()), (0, 10))

# Date Range Picker for ICU Admission
start_date, end_date = st.sidebar.date_input("Select Admission Date Range", 
                                             [pd.to_datetime("2125-01-01"), pd.to_datetime("2165-01-01")])

# Convert `intime` to datetime and drop invalid rows
merged_data["intime"] = pd.to_datetime(merged_data["intime"], errors='coerce')
filtered_data = merged_data.dropna(subset=["intime"])

# Apply Filters
filtered_data = filtered_data[
    (filtered_data["first_careunit"].isin(care_unit_filter)) &
    (filtered_data["label"].isin(measurement_filter)) &
    (filtered_data["los"].between(los_range[0], los_range[1])) &
    (filtered_data["intime"].between(start_date, end_date))
]

# Main Dashboard Title
st.title("ICU Management Dashboard")

# Metrics
st.subheader("Key Metrics")
total_patients = filtered_data["subject_id"].nunique()
average_los = filtered_data["los"].mean()
num_measurements = filtered_data["label"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Patients", total_patients)
col2.metric("Average LOS (days)", f"{average_los:.2f}")
col3.metric("Unique Measurements", num_measurements)

# Pie Chart: ICU Care Unit Distribution
st.subheader("ICU Care Unit Distribution")
care_unit_dist = filtered_data["first_careunit"].value_counts().reset_index()
care_unit_dist.columns = ["Care Unit", "Count"]
fig_pie = px.pie(care_unit_dist, names="Care Unit", values="Count", title="Care Unit Distribution")
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

# Correlation Heatmap
st.subheader("Correlation Heatmap")
numeric_cols = filtered_data[["los", "valuenum"]].dropna()
if not numeric_cols.empty:
    fig, ax = plt.subplots()
    sns.heatmap(numeric_cols.corr(), annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)
else:
    st.warning("No numerical data available to display the heatmap.")

# Summary Table: ICU Care Unit Summary
st.subheader("ICU Care Unit Summary")
icu_summary = filtered_data.groupby("first_careunit").agg(
    Total_Stays=("icustay_id", "count"),
    Avg_LOS=("los", "mean")
).reset_index()
st.dataframe(icu_summary)

# Filtered Data Preview
st.write("### Filtered Data Preview")
st.dataframe(filtered_data.head())
