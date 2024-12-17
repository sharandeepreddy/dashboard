import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Load and process data
@st.cache_data
def load_data():
    # Load datasets
    chart_event = pd.read_csv("CHARTEVENTS.csv", usecols=['icustay_id', 'itemid', 'charttime', 'value', 'valuenum', 'valueuom', 'error'])
    d_item = pd.read_csv("D_ITEMS.csv")
    icu_stay = pd.read_csv("ICUSTAYS.csv")
    
    # Clean data
    chart_event = chart_event.loc[chart_event['error'] != 1]
    chart_event.drop(['error'], axis=1, inplace=True)

    # Merge datasets
    ventilation = pd.merge(chart_event, d_item, on='itemid')
    ventilation = pd.merge(ventilation, icu_stay, on='icustay_id')

    # Filter selected labels
    selected = ['Respiratory Rate', 'Heart Rate', 'Non Invasive Blood Pressure mean', 'Non Invasive Blood Pressure diastolic']
    ventilation = ventilation.loc[ventilation['label'].isin(selected)]

    # Convert time to hours
    ventilation['charttime'] = pd.to_datetime(ventilation['charttime'])
    ventilation['intime'] = pd.to_datetime(ventilation['intime'])
    ventilation['icu_time'] = (ventilation['charttime'] - ventilation['intime']).dt.total_seconds() / 3600
    ventilation.drop(['intime', 'outtime', 'conceptid'], axis=1, inplace=True)

    return ventilation

# Load data
ventilation = load_data()

# Sidebar Filters
st.sidebar.title("Filters")
label_filter = st.sidebar.multiselect("Select Measurement Types", ventilation["label"].unique(), default=ventilation["label"].unique())
icu_time_range = st.sidebar.slider("Select ICU Time Range (hours)", int(ventilation['icu_time'].min()), int(ventilation['icu_time'].max()), 
                                   (0, int(ventilation['icu_time'].max())))

# Filtered Data
filtered_data = ventilation[
    (ventilation["label"].isin(label_filter)) & 
    (ventilation["icu_time"].between(icu_time_range[0], icu_time_range[1]))
]

# Main Dashboard Title
st.title("ICU Ventilation Dashboard")

# Metrics
st.subheader("Key Metrics")
total_patients = filtered_data["icustay_id"].nunique()
st.metric("Total ICU Stays", total_patients)

# Line Chart: ICU Time vs Measurement Value
st.subheader("Measurement Trends Over ICU Time")
fig_line = px.line(filtered_data, x="icu_time", y="valuenum", color="label", title="ICU Time vs Measurement Value",
                   labels={"icu_time": "ICU Time (hours)", "valuenum": "Measurement Value"})
st.plotly_chart(fig_line)

# Scatter Plot
st.subheader("Scatter Plot: ICU Time vs Measurement Value")
fig_scatter = px.scatter(filtered_data, x="icu_time", y="valuenum", color="label",
                         title="ICU Time vs Measurement Value",
                         labels={"icu_time": "ICU Time (hours)", "valuenum": "Measurement Value"})
st.plotly_chart(fig_scatter)

# Bar Chart: Measurement Distribution
st.subheader("Distribution of Measurement Types")
fig_bar = px.bar(filtered_data['label'].value_counts().reset_index(), x='index', y='label', 
                 labels={"index": "Measurement Type", "label": "Count"}, title="Measurement Distribution")
st.plotly_chart(fig_bar)

# Data Preview
st.subheader("Filtered Data Preview")
st.dataframe(filtered_data.head())
