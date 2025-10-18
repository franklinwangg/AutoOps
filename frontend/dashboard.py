# frontend/dashboard.py
import streamlit as st
import pandas as pd
import json
from time import sleep

# --- Page Configuration ---
st.set_page_config(
    page_title="AutoOps AI Dashboard",
    page_icon="🤖",
    layout="wide"
)

# --- App Title ---
st.title("🤖 AutoOps: AI-Powered Self-Healing System")
st.markdown("This dashboard shows the real-time status of our microservices and the corrective actions taken by our AI agent.")

# --- Helper Functions ---
def load_data(file_path):
    """Loads a JSON-lines file into a Pandas DataFrame."""
    try:
        return pd.read_json(file_path, lines=True)
    except (FileNotFoundError, ValueError):
        return pd.DataFrame()

# --- Main App Layout ---
# Create columns for the layout
col_summary, col_actions = st.columns(2)

with col_summary:
    st.header("📊 Live System Health")
    summary_placeholder = st.empty()

with col_actions:
    st.header("🧠 AI Agent Actions")
    actions_placeholder = st.empty()

st.header("📜 Raw Service Logs")
logs_placeholder = st.empty()

# --- Auto-Refreshing Loop ---
while True:
    # Load data from log files
    logs_df = load_data("data/logs.json").tail(200) # Keep last 200 log entries
    actions_df = load_data("data/agent_actions.json").tail(10) # Keep last 10 actions

    # --- Update Summary Section ---
    with summary_placeholder.container():
        if not logs_df.empty:
            # Calculate key metrics
            latest_logs = logs_df.drop_duplicates(subset='service', keep='last')
            uptime_df = logs_df.groupby('service')['status_code'].apply(
                lambda x: (x == 200).sum() / len(x) * 100 if len(x) > 0 else 0
            ).reset_index(name='uptime (%)')

            st.dataframe(latest_logs[['timestamp', 'service', 'status_code', 'latency_ms']], use_container_width=True)
            st.dataframe(uptime_df, use_container_width=True)

            # Chart of latency over time
            st.line_chart(logs_df.pivot_table(index='timestamp', columns='service', values='latency_ms'))
        else:
            st.warning("Waiting for monitoring data...")

    # --- Update AI Actions Section ---
    with actions_placeholder.container():
        if not actions_df.empty:
            st.dataframe(actions_df[['timestamp', 'action', 'service_name', 'reason']], use_container_width=True)
        else:
            st.info("No AI actions have been recorded yet.")
            
    # --- Update Raw Logs Section ---
    with logs_placeholder.container():
        if not logs_df.empty:
            st.text_area("Latest Logs", "\n".join(logs_df.to_json(orient='records', lines=True).strip().split('\n')[-20:]), height=300)
        else:
            st.warning("Log file is empty.")

    # Wait for 2 seconds before refreshing
    sleep(2)