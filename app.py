import streamlit as st
import pandas as pd
import plotly.express as px

# Load datasets
@st.cache_data
def load_data():
    try:
        chart_events = pd.read_csv("CHARTEVENTS.csv", nrows=5000)
        d_items = pd.read_csv("D_ITEMS.csv")
        icu_stays = pd.read_csv("ICUSTAYS.csv")
        return chart_events, d_items, icu_stays
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return None, None, None

chart_events, d_items, icu_stays = load_data()

# Stop execution if data is not loaded
if chart_events is None or d_items is None or icu_stays is None:
    st.stop()

# Predefined filters for simplicity
care_unit_options = ["MICU", "CCU", "SICU", "TSICU"]
measurement_options = ["Heart Rate", "Blood Pressure", "Oxygen Saturation"]

# Filter D_ITEMS to only include relevant measurements
filtered_items = d_items[d_items["label"].isin(measurement_options)]

# Merge datasets
merged_data = pd.merge(chart_events, icu_stays, on="icustay_id", how="inner", suffixes=('_chart', '_icu'))
merged_data = pd.merge(merged_data, filtered_items, on="itemid", how="inner")

# Sidebar filters
st.sidebar.title("Filters")
selected_unit = st.sidebar.selectbox("Select Care Unit", care_unit_options)
selected_year = st.sidebar.slider("Select Year Range", 2125, 2165, (2130, 2150))
selected_item = st.sidebar.selectbox("Select Measurement", measurement_options)

# Filter data based on selections
filtered_data = merged_data[
    (merged_data["first_careunit"] == selected_unit) &
    (pd.to_datetime(merged_data["intime"]).dt.year.between(*selected_year)) &
    (merged_data["label"] == selected_item)
]

# Main Dashboard
st.title("ICU Data Dashboard")
st.write(f"### Selected Care Unit: {selected_unit} | Measurement: {selected_item} | Years: {selected_year[0]}–{selected_year[1]}")

# Key Metrics
st.subheader("Key Metrics")
if filtered_data.empty:
    st.warning("No data available for the selected filters.")
    avg_los = 0
    total_patients = 0
else:
    avg_los = filtered_data["los"].mean()
    total_patients = filtered_data["subject_id"].nunique()

st.metric("Average Length of Stay (days)", f"{avg_los:.2f}")
st.metric("Total Patients", total_patients)

# Visualizations
if not filtered_data.empty:
    # Scatter Plot: Length of Stay vs. Measurement Value
    st.subheader("Length of Stay vs. Measurement Value")
    fig_scatter = px.scatter(
        filtered_data, 
        x="los", y="valuenum", 
        title=f"Length of Stay vs {selected_item} Values",
        labels={"los": "Length of Stay (days)", "valuenum": selected_item}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Bar Chart: Patient Distribution by Care Unit
    st.subheader("Patient Distribution by Care Unit")
    care_unit_count = filtered_data["first_careunit"].value_counts().reset_index()
    care_unit_count.columns = ["Care Unit", "Count"]
    fig_bar = px.bar(
        care_unit_count, x="Care Unit", y="Count", 
        title="Number of Patients by Care Unit"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.write("No data available for the selected filters.")
