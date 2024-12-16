import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Title and description
st.title("ICU Ventilation Equipment Dashboard")
st.write("An interactive dashboard to explore ICU ventilation data insights using the MIMIC-III dataset.")

# Sidebar for user inputs
st.sidebar.header("User Inputs")

# File upload
chart_file = st.sidebar.file_uploader("Upload CHARTEVENTS.csv", type=['csv'])
item_file = st.sidebar.file_uploader("Upload D_ITEMS.csv", type=['csv'])
stay_file = st.sidebar.file_uploader("Upload ICUSTAYS.csv", type=['csv'])

if chart_file and item_file and stay_file:
    # Load datasets
    st.write("### Dataset Loading")
    chart_event = pd.read_csv(chart_file, usecols=['icustay_id', 'itemid', 'charttime', 'value', 'valuenum', 'valueuom', 'error'])
    chart_event = chart_event.loc[chart_event['error'] != 1]
    chart_event.drop(['error'], axis=1, inplace=True)

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

    # Sidebar interactive components
    st.sidebar.header("Filters and Parameters")
    selected_label = st.sidebar.selectbox("Select Variable to Explore", selected)
    time_range = st.sidebar.slider("ICU Time Range (hours)", int(ventilation['icu_time'].min()), int(ventilation['icu_time'].max()), (0, 48))
    ventilation_filtered = ventilation[(ventilation['label'] == selected_label) & (ventilation['icu_time'].between(*time_range))]

    # Display filtered data
    st.write(f"### Filtered Data ({selected_label})")
    st.dataframe(ventilation_filtered.head())

    # Summary statistics
    st.write("### Key Metrics")
    mean_val = ventilation_filtered['valuenum'].mean()
    median_val = ventilation_filtered['valuenum'].median()
    st.metric(label="Mean Value", value=f"{mean_val:.2f}")
    st.metric(label="Median Value", value=f"{median_val:.2f}")

    # Visualizations
    st.write("### Visualizations")

    # Distribution plot
    st.write(f"Distribution of {selected_label}")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.histplot(ventilation_filtered['valuenum'], kde=True, bins=30, ax=ax, color='blue')
    ax.set_title(f"Distribution of {selected_label}")
    st.pyplot(fig)

    # Correlation heatmap
    st.write("Correlation Heatmap")
    numeric_columns = ventilation_filtered.select_dtypes(include=[np.number])
    corr = numeric_columns.corr()  # Use only numeric columns for correlation
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    st.pyplot(fig)

    # Trend over time
    st.write("Trend Over Time")
    ventilation_filtered['hour'] = ventilation_filtered['charttime'].dt.hour
    avg_by_hour = ventilation_filtered.groupby('hour')['valuenum'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.lineplot(data=avg_by_hour, x='hour', y='valuenum', ax=ax, marker='o')
    ax.set_title(f"Hourly Trend of {selected_label}")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Average Value")
    st.pyplot(fig)

else:
    st.warning("Please upload all required files.")
