import os
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Severity classification based on AQI
# -----------------------------
def classify_severity(aqi):
    if aqi <= 50:
        return "Normal"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "High"
    elif aqi <= 200:
        return "Violation"
    else:
        return "Severe"

def show_public():
    st.title("🌱 EcoProof Public Dashboard")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # Support both raw and processed CSV
    processed_csv = os.path.join(DATA_DIR, "sensor_data_with_anomalies.csv")
    raw_csv = os.path.join(DATA_DIR, "sensor_data_raw.csv")

    if os.path.exists(processed_csv):
        csv_path = processed_csv
    elif os.path.exists(raw_csv):
        csv_path = raw_csv
    else:
        st.error("❌ No sensor data file found. Please upload sensor data via the Admin Dashboard.")
        return

    # -----------------------------
    # Load and prepare data
    # -----------------------------
    try:
        data = pd.read_csv(csv_path)
        data.columns = data.columns.str.strip().str.lower()

        # Compute anomaly columns if not already present
        if 'anomaly_severity' not in data.columns:
            data['anomaly_severity'] = data['aqi'].apply(classify_severity)
        if 'anomaly_flag' not in data.columns:
            data['anomaly_flag'] = data['anomaly_severity'] != "Normal"

    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        return

    # -----------------------------
    # Plant search
    # -----------------------------
    st.subheader("🔍 Search by Plant")
    plant_input = st.text_input("Enter Plant Name or Plant ID:")

    if not plant_input:
        st.info("Enter a Plant Name or Plant ID to view data.")

        # Show available plants as a helper
        if 'plant_name' in data.columns and 'plant_id' in data.columns:
            plants = data[['plant_name', 'plant_id']].drop_duplicates().reset_index(drop=True)
            st.markdown("**Available Plants:**")
            st.dataframe(plants, use_container_width=True)
        return

    # -----------------------------
    # Filter data for selected plant
    # -----------------------------
    plant_data = data.copy()
    if 'plant_name' in data.columns:
        plant_data = plant_data[
            (plant_data['plant_name'].str.lower() == plant_input.lower()) |
            (plant_data['plant_id'].astype(str) == plant_input)
        ]
    else:
        st.error("❌ CSV is missing 'plant_name' or 'plant_id' columns.")
        return

    if plant_data.empty:
        st.warning("⚠️ Plant not found. Please check the name or ID.")
        return

    latest = plant_data.iloc[-1]
    pollutants = [p for p in ['pm2_5', 'pm10', 'so2_level', 'no2_level', 'aqi'] if p in data.columns]
    severity_colors = {
        "Normal": "green",
        "Moderate": "yellow",
        "High": "orange",
        "Violation": "red",
        "Severe": "darkred"
    }

    # -----------------------------
    # KPI Cards
    # -----------------------------
    st.subheader("💨 Current Pollutant Levels")
    kpi_cols = st.columns(len(pollutants))
    for i, pollutant in enumerate(pollutants):
        if pollutant in latest:
            kpi_cols[i].metric(label=pollutant.upper(), value=round(latest[pollutant], 2))

    # -----------------------------
    # Bar chart
    # -----------------------------
    st.subheader("📊 Latest Pollutant Levels")
    severity = latest['anomaly_severity'] if latest['anomaly_flag'] else "Normal"
    bar_data = pd.DataFrame({
        "Pollutant": pollutants,
        "Value": [round(latest[p], 2) for p in pollutants],
        "Severity": [severity] * len(pollutants)
    })
    fig_bar = px.bar(
        bar_data, x="Pollutant", y="Value",
        color="Severity", color_discrete_map=severity_colors,
        text="Value"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------
    # Time series
    # -----------------------------
    if 'timestamp' in data.columns:
        st.subheader("📈 Pollutant Levels Over Time")
        fig_line = px.line(
            plant_data, x="timestamp", y=pollutants,
            title=f"{latest.get('plant_name', plant_input)} Emission Trends"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # -----------------------------
    # Anomalies table & pie chart
    # -----------------------------
    st.subheader("⚠️ Anomalies")
    anomalies = plant_data[plant_data['anomaly_flag'] == True]

    if not anomalies.empty:
        display_cols = [c for c in ['timestamp', 'pm2_5', 'pm10', 'so2_level', 'no2_level', 'aqi', 'anomaly_severity'] if c in anomalies.columns]
        st.dataframe(anomalies[display_cols], use_container_width=True)

        pie_data = anomalies['anomaly_severity'].value_counts().reset_index()
        pie_data.columns = ['Severity', 'Count']
        fig_pie = px.pie(
            pie_data, names='Severity', values='Count',
            color='Severity', color_discrete_map=severity_colors
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No anomalies detected for this plant.")

    # -----------------------------
    # Pollution verdict
    # -----------------------------
    st.subheader("🌡 Pollution Verdict")
    if anomalies.empty:
        st.success("✅ Plant is operating within normal limits.")
    else:
        severity_mapping = {"Normal": 0, "Moderate": 1, "High": 2, "Violation": 3, "Severe": 4}
        max_severity = anomalies['anomaly_severity'].map(severity_mapping).max()
        if max_severity <= 1:
            st.warning("⚠️ Plant has moderate pollution levels.")
        elif max_severity <= 2:
            st.warning("🟠 Plant has high pollution levels.")
        else:
            st.error("❌ Plant is polluting more than allowed!")
