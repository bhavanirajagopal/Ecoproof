import streamlit as st
import pandas as pd
import json
import hashlib
from blockchain_core import Blockchain


def show_admin():
    try:
        st.set_page_config(page_title="Admin Dashboard", layout="wide")
    except st.errors.StreamlitAPIException:
        pass  # Already configured

    st.title("🌐 Admin Dashboard - Emissions Monitoring")

    # -------------------------
    # Initialize Blockchain
    # -------------------------
    if "blockchain_instance" not in st.session_state:
        st.session_state.blockchain_instance = Blockchain()
    bc = st.session_state.blockchain_instance

    # -------------------------
    # File Upload
    # -------------------------
    st.subheader("📡 Sensor Data")
    uploaded_file = st.file_uploader("Upload sensor_data_raw.csv", type="csv")

    if uploaded_file is None:
        st.info("Please upload a CSV file to begin.")
        return

    try:
        df = pd.read_csv(uploaded_file).head(300)
        if df.empty:
            st.warning("No data available.")
            return
        st.dataframe(df.tail(10), use_container_width=True)
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        return

    # -------------------------
    # Threshold Settings
    # -------------------------
    st.sidebar.header("⚙ Set Thresholds")
    thresholds = {
        "co_level": {"warning": 400, "critical": 500},
        "no2_level": {"warning": 50, "critical": 80},
        "pm2_5": {"warning": 35, "critical": 75},
        "pm10": {"warning": 50, "critical": 100}
    }
    for pollutant in thresholds:
        thresholds[pollutant]["warning"] = st.sidebar.number_input(
            f"{pollutant} warning threshold", value=thresholds[pollutant]["warning"],
            key=f"{pollutant}_warning"
        )
        thresholds[pollutant]["critical"] = st.sidebar.number_input(
            f"{pollutant} critical threshold", value=thresholds[pollutant]["critical"],
            key=f"{pollutant}_critical"
        )

    # -------------------------
    # Anomaly Detection
    # -------------------------
    anomaly_rows = []
    df_with_anomalies = df.copy()
    df_with_anomalies["anomaly_flag"] = False
    df_with_anomalies["critical_flag"] = False
    df_with_anomalies["anomaly_details"] = ""

    with st.spinner("🔍 Detecting anomalies..."):
        for idx, row in df.iterrows():
            anomaly_flag = False
            critical_flag = False
            alert_details = []

            for pollutant, vals in thresholds.items():
                if pollutant in row and pd.notna(row[pollutant]):
                    try:
                        value = float(row[pollutant])
                        if value > vals["warning"]:
                            anomaly_flag = True
                        if value > vals["critical"]:
                            critical_flag = True
                            alert_details.append(f"{pollutant}={value}")
                    except (ValueError, TypeError):
                        continue

            if anomaly_flag:
                anomaly_data = {
                    "plant_id": row.get('plant_id'),
                    "plant_name": row.get('plant_name'),
                    "timestamp": row.get('timestamp'),
                    "anomaly_details": alert_details,
                    "alert_sent": critical_flag
                }
                if not bc.is_row_logged(anomaly_data):
                    bc.add_block(anomaly_data)
                    anomaly_rows.append(anomaly_data)

                df_with_anomalies.at[idx, "anomaly_flag"] = True
                df_with_anomalies.at[idx, "critical_flag"] = critical_flag
                df_with_anomalies.at[idx, "anomaly_details"] = ", ".join(alert_details)

    # -------------------------
    # Display Anomalies
    # -------------------------
    if anomaly_rows:
        st.subheader("🚨 Latest Anomalies Detected")
        st.dataframe(pd.DataFrame(anomaly_rows), use_container_width=True)
    else:
        st.success("✅ No new anomalies detected")

    # -------------------------
    # Download Anomalies CSV
    # -------------------------
    anomaly_csv = df_with_anomalies.to_csv(index=False)
    st.download_button(
        label="📥 Download Anomalies CSV",
        data=anomaly_csv,
        file_name="sensor_data_with_anomalies.csv",
        mime="text/csv",
        key="download_anomalies"
    )

    # -------------------------
    # Blockchain Tamper Check
    # -------------------------
    if st.button("🔍 Validate Blockchain"):
        if bc.is_chain_valid():
            st.success("✅ Blockchain is valid and secure!")
        else:
            st.error("⚠️ Blockchain integrity compromised!")

    # -------------------------
    # Download Blockchain JSON
    # -------------------------
    chain_data = [block.to_dict() for block in bc.chain]
    chain_json = json.dumps(chain_data, indent=4, default=str)
    st.download_button(
        label="📥 Download Blockchain JSON",
        data=chain_json,
        file_name="blockchain_data.json",
        mime="application/json",
        key="download_blockchain"
    )
