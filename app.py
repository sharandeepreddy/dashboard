import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Title and description
st.title("ICU Ventilation Equipment Dashboard")
st.write("This dashboard predicts ventilation equipment needs using the MIMIC-III dataset.")

# File upload
st.sidebar.header("Upload Dataset Files")
chart_file = st.sidebar.file_uploader("Upload CHARTEVENTS.csv", type=['csv'])
item_file = st.sidebar.file_uploader("Upload D_ITEMS.csv", type=['csv'])
stay_file = st.sidebar.file_uploader("Upload ICUSTAYS.csv", type=['csv'])

if chart_file and item_file and stay_file:
    # Load datasets
    st.write("### Dataset Loading")
    chart_event = pd.read_csv(chart_file, usecols=['icustay_id', 'itemid', 'charttime', 'value', 'valuenum', 'valueuom', 'error'])
    chart_event = chart_event.loc[chart_event['error'] != 1]
    chart_event.drop(['error'], axis=1, inplace=True)
    st.write("CHARTEVENTS loaded:", chart_event.head())

    d_item = pd.read_csv(item_file)
    icu_stay = pd.read_csv(stay_file)

    # Merge datasets
    ventilation = pd.merge(chart_event, d_item, on='itemid')
    ventilation = pd.merge(ventilation, icu_stay, on='icustay_id')

    # Feature selection and processing
    selected = ['Respiratory Rate', 'Heart Rate', 'Non Invasive Blood Pressure mean', 'Non Invasive Blood Pressure diastolic']
    ventilation = ventilation.loc[ventilation['label'].isin(selected)]
    ventilation['charttime'] = pd.to_datetime(ventilation['charttime'])
    ventilation['intime'] = pd.to_datetime(ventilation['intime'])
    ventilation['icu_time'] = (ventilation['charttime'] - ventilation['intime']).dt.total_seconds() / 3600
    ventilation.drop(['intime', 'outtime', 'conceptid'], axis=1, inplace=True)
    ventilation['patient_id'] = np.arange(1, len(ventilation) + 1)

    # Display merged dataset
    st.write("### Merged Dataset")
    st.dataframe(ventilation.head())

    # Handle missing data
    st.write("### Missing Data Analysis")
    missing_data = ventilation.isnull().sum()
    st.write(missing_data)

    # Feature engineering
    ventilation['year'] = ventilation['charttime'].dt.year
    ventilation['month'] = ventilation['charttime'].dt.month
    ventilation['day'] = ventilation['charttime'].dt.day
    ventilation['hour'] = ventilation['charttime'].dt.hour
    ventilation['minute'] = ventilation['charttime'].dt.minute
    ventilation['second'] = ventilation['charttime'].dt.second
    ventilation.drop(['charttime'], axis=1, inplace=True)

    # Visualizations
    st.write("### Visualizations")

    # Correlation heatmap
    st.write("Correlation Heatmap")
    corr = ventilation.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
    st.pyplot(plt)

    # Distribution of ICU times
    st.write("ICU Time Distribution")
    plt.figure(figsize=(8, 6))
    sns.histplot(ventilation['icu_time'], kde=True, bins=30, color='blue')
    plt.title("ICU Time Distribution")
    st.pyplot(plt)

else:
    st.warning("Please upload all required files.")
