# public_dashboard.py

import streamlit as st
import pandas as pd

# -------------------------
# Anomaly Detection Function
# -------------------------
def detect_anomalies(df):
    numeric_cols = ['pm2_5', 'pm10', 'so2_level', 'no2_level', 'aqi']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['anomaly_flag'] = False
    df['anomaly_severity'] = 'Normal'

    # Moderate anomalies
    moderate_mask = (
        (df['pm2_5'].between(186, 269)) |
        (df['pm10'].between(239, 350)) |
        (df['so2_level'].between(87, 125)) |
        (df['no2_level'].between(121, 177)) |
        (df['aqi'].between(178, 223))
    )
    df.loc[moderate_mask, ['anomaly_flag', 'anomaly_severity']] = [True, 'Moderate']

    # High anomalies
    high_mask = (
        (df['pm2_5'].between(269, 341)) |
        (df['pm10'].between(350, 430)) |
        (df['so2_level'].between(125, 152)) |
        (df['no2_level'].between(177, 217)) |
        (df['aqi'].between(223, 263))
    )
    df.loc[high_mask, ['anomaly_flag', 'anomaly_severity']] = [True, 'High']

    # Violation anomalies
    violation_mask = (
        (df['pm2_5'].between(341, 372)) |
        (df['pm10'].between(430, 464)) |
        (df['so2_level'].between(152, 167)) |
        (df['no2_level'].between(217, 234)) |
        (df['aqi'].between(263, 291))
    )
    df.loc[violation_mask, ['anomaly_flag', 'anomaly_severity']] = [True, 'Violation']

    # Severe anomalies
    severe_mask = (
        (df['pm2_5'] > 372) |
        (df['pm10'] > 464) |
        (df['so2_level'] > 167) |
        (df['no2_level'] > 234) |
        (df['aqi'] > 291)
    )
    df.loc[severe_mask, ['anomaly_flag', 'anomaly_severity']] = [True, 'Severe']

    return df

# -------------------------
# Streamlit UI
# -------------------------
st.title("🌿 EcoProof: Air Quality Anomaly Detection")

st.markdown("""
Upload your CSV file containing the following columns:  
`pm2_5`, `pm10`, `so2_level`, `no2_level`, `aqi`
""")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df_with_anomalies = detect_anomalies(df)

        st.subheader("✅ Anomaly Detection Results")
        st.dataframe(df_with_anomalies)

        # Download button
        csv = df_with_anomalies.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV with Anomalies",
            data=csv,
            file_name="sensor_data_with_anomalies.csv",
            mime="text/csv"
        )

        st.success("Anomalies detected successfully!")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("Please upload a CSV file to start anomaly detection.")