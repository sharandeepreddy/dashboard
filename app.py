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
chart_events = chart_events.dropna(subset=["itemid", "valuenum"])
merged_data = pd.merge(
    chart_events, 
    icu_stays[['icustay_id', 'los', 'first_careunit']], 
    on="icustay_id", 
    how="inner"
)
merged_data = pd.merge(merged_data, d_items[['itemid', 'label']], on="itemid", how="inner")

# Check if 'icustay_id' exists
if 'icustay_id' not in merged_data.columns:
    st.error("'icustay_id' column is missing after merging. Check the datasets.")
    st.stop()

# Sidebar Filters
st.sidebar.title("Filters")
care_unit_filter = st.sidebar.multiselect(
    "Select Care Units", 
    icu_stays["first_careunit"].unique(), 
    default=icu_stays["first_careunit"].unique()
)

# Filter Data
filtered_data = merged_data[merged_data["first_careunit"].isin(care_unit_filter)]

# Main Dashboard Title
st.title("ICU Management Dashboard")

# Metrics
st.subheader("Key Metrics")
total_patients = filtered_data["icustay_id"].nunique()
average_los = filtered_data["los"].mean()

col1, col2 = st.columns(2)
col1.metric("Total ICU Stays", total_patients)
col2.metric("Average Length of Stay (LOS)", f"{average_los:.2f} days")

# Interactive Line Chart for Monitoring Types
st.subheader("ICU Monitoring Types Over Time")

# Replace 'subject_id' with 'icustay_id' for plotting
data1 = filtered_data[filtered_data['label'] == "Heart Rate"]
data2 = filtered_data[filtered_data['label'] == "Blood Pressure Diastolic"]
data3 = filtered_data[filtered_data['label'] == "Blood Pressure Mean"]
data4 = filtered_data[filtered_data['label'] == "Respiratory Rate"]

fig_line = go.Figure()

# Add traces with 'icustay_id' instead of 'subject_id'
fig_line.add_trace(go.Scatter(x=data1['icustay_id'], y=data1['valuenum'], 
                              mode='lines', name='Heart Rate', line=dict(color='red')))
fig_line.add_trace(go.Scatter(x=data2['icustay_id'], y=data2['valuenum'], 
                              mode='lines', name='Blood Pressure Diastolic', line=dict(color='yellow')))
fig_line.add_trace(go.Scatter(x=data3['icustay_id'], y=data3['valuenum'], 
                              mode='lines', name='Blood Pressure Mean', line=dict(color='blue')))
fig_line.add_trace(go.Scatter(x=data4['icustay_id'], y=data4['valuenum'], 
                              mode='lines', name='Respiratory Rate', line=dict(color='green')))

fig_line.update_layout(
    title="ICU Monitoring Types Over ICU Stay IDs",
    xaxis_title="ICU Stay ID",
    yaxis_title="Measurement Value",
    legend_title="Monitoring Type"
)
st.plotly_chart(fig_line)

# Filtered Data Preview
st.subheader("Filtered Data Preview")
st.dataframe(filtered_data.head())
