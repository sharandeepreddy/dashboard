import streamlit as st
import pandas as pd
import plotly.express as px

# Load datasets (sampled for performance; in real deployment, optimize or use a database)
@st.cache_data
def load_data():
    chart_events = pd.read_csv("CHARTEVENTS.csv", nrows=1000)
    d_items = pd.read_csv("D_ITEMS.csv")
    icu_stays = pd.read_csv("ICUSTAYS.csv")
    return chart_events, d_items, icu_stays

chart_events, d_items, icu_stays = load_data()

# Merge datasets for meaningful insights
merged_data = pd.merge(chart_events, icu_stays, on="icustay_id", how="inner")
merged_data = pd.merge(merged_data, d_items, on="itemid", how="inner")

# Sidebar filters
st.sidebar.title("Filters")
selected_unit = st.sidebar.multiselect("Select Care Unit", icu_stays["first_careunit"].unique())
selected_year = st.sidebar.slider("Select Year Range", 2125, 2165, (2130, 2150))
selected_item = st.sidebar.selectbox("Select Measurement", d_items["label"].unique())

# Filter data based on selections
filtered_data = merged_data[
    (merged_data["first_careunit"].isin(selected_unit)) &
    (pd.to_datetime(merged_data["intime"]).dt.year.between(*selected_year)) &
    (merged_data["label"] == selected_item)
]

# Main Dashboard
st.title("ICU Dashboard")

# Key Metrics
st.subheader("Key Metrics")
avg_los = filtered_data["los"].mean() if not filtered_data.empty else 0
total_patients = filtered_data["subject_id"].nunique()
st.metric("Average Length of Stay (days)", f"{avg_los:.2f}")
st.metric("Total Patients", total_patients)

# Visualizations
st.subheader("Visualizations")

# Bar Chart: Patients by Care Unit
if not filtered_data.empty:
    care_unit_count = filtered_data["first_careunit"].value_counts().reset_index()
    care_unit_count.columns = ["Care Unit", "Count"]
    fig_bar = px.bar(care_unit_count, x="Care Unit", y="Count", title="Patients by Care Unit")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.write("No data available for the selected filters.")

# Scatter Plot: Length of Stay vs. Measurement Value
if not filtered_data.empty:
    fig_scatter = px.scatter(
        filtered_data, 
        x="los", y="valuenum", 
        color="first_careunit", 
        title="Length of Stay vs. Measurement Value",
        labels={"los": "Length of Stay (days)", "valuenum": "Measurement Value"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.write("No data available for the selected filters.")

# Summary Text
st.subheader("Summary")
if not filtered_data.empty:
    st.write(f"The selected measurement '{selected_item}' shows an average value of "
             f"{filtered_data['valuenum'].mean():.2f} across all patients.")
else:
    st.write("No data available for the selected filters.")
