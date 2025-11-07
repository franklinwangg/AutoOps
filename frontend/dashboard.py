# # frontend/dashboard.py
# import streamlit as st
# import pandas as pd
# import json
# from time import sleep
# import os 

# st.set_page_config(
#     page_title="AutoOps AI Dashboard",
#     page_icon="🤖",
#     layout="wide"
# )
# st.title("🤖 AutoOps: AI-Powered Self-Healing System")
# st.markdown("This dashboard shows the real-time status of our microservices and the corrective actions taken by our AI agent.")

# FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

# DATA_DIR = os.path.join(FRONTEND_DIR, '..', 'data')
# LOG_FILE = os.path.join(DATA_DIR, 'logs.json')
# ACTION_LOG_FILE = os.path.join(DATA_DIR, 'agent_actions.json')


# def load_data(file_path):
#     """Loads a JSON-lines file into a Pandas DataFrame."""
#     try:

#         if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
#             return pd.read_json(file_path, lines=True)
#     except (FileNotFoundError, ValueError, pd.errors.EmptyDataError):
#         pass 
#     return pd.DataFrame()

# col_summary, col_actions = st.columns(2)

# with col_summary:
#     st.header("📊 Live System Health")
#     summary_placeholder = st.empty()

# with col_actions:
#     st.header("🧠 AI Agent Actions")
#     actions_placeholder = st.empty()

# st.header("📜 Raw Service Logs")
# logs_placeholder = st.empty()

# while True:

#     logs_df = load_data(LOG_FILE).tail(200)
#     actions_df = load_data(ACTION_LOG_FILE).tail(10)

#     with summary_placeholder.container():
#         if not logs_df.empty:
#             latest_logs = logs_df.drop_duplicates(subset='service', keep='last')
#             uptime_df = logs_df.groupby('service')['status_code'].apply(
#                 lambda x: (x == 200).sum() / len(x) * 100 if len(x) > 0 else 0
#             ).reset_index(name='uptime (%)')

#             st.dataframe(latest_logs[['timestamp', 'service', 'status_code', 'latency_ms']], use_container_width=True)
#             st.dataframe(uptime_df, use_container_width=True)

#             logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
#             st.line_chart(logs_df.pivot_table(index='timestamp', columns='service', values='latency_ms'))
#         else:
#             st.warning("Waiting for monitoring data... (Make sure monitor.py is running)")

#     with actions_placeholder.container():
#         if not actions_df.empty:
#             st.dataframe(actions_df[['timestamp', 'action', 'service_name', 'reason']].tail(5), use_container_width=True)
#         else:
#             st.info("No AI actions have been recorded yet. (Make sure healer.py is running)")
#     with logs_placeholder.container():
#         if not logs_df.empty:
#             log_lines = logs_df.to_json(orient='records', lines=True).strip().split('\n')
#             st.text_area("Latest Logs", "\n".join(log_lines[-20:]), height=300)
#         else:
#             st.warning("Log file is empty.")

#     sleep(2)

import streamlit as st
import pandas as pd
import json
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AutoOps Dashboard", layout="wide")
st.title("🤖 AutoOps: AI-Powered Self-Healing System")

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
LOG_FILE = os.path.join(DATA_DIR, 'logs.json')
ACTION_LOG_FILE = os.path.join(DATA_DIR, 'agent_actions.json')

# Auto-refresh every 2 seconds
st_autorefresh(interval=15000, key="data_refresh")

def load_data(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_json(file_path, lines=True)
        except Exception:
            pass
    return pd.DataFrame()

logs_df = load_data(LOG_FILE).tail(200)
actions_df = load_data(ACTION_LOG_FILE).tail(10)

col_summary, col_actions = st.columns(2)
with col_summary:
    st.header("📊 Live System Health")
    if not logs_df.empty:
        latest_logs = logs_df.drop_duplicates(subset='service', keep='last')
        uptime_df = logs_df.groupby('service')['status_code'].apply(
            lambda x: (x == 200).sum() / len(x) * 100 if len(x) > 0 else 0
        ).reset_index(name='uptime (%)')

        st.dataframe(latest_logs[['timestamp', 'service', 'status_code', 'latency_ms']], use_container_width=True)
        st.dataframe(uptime_df, use_container_width=True)
    else:
        st.warning("Waiting for monitoring data...")

with col_actions:
    st.header("🧠 AI Agent Actions")
    if not actions_df.empty:
        st.dataframe(actions_df[['timestamp', 'action', 'service_name', 'reason']].tail(5), use_container_width=True)
    else:
        st.info("No AI actions have been recorded yet.")

st.header("📜 Raw Logs")
if not logs_df.empty:
    log_lines = logs_df.to_json(orient='records', lines=True).split('\n')
    st.text_area("Latest Logs", "\n".join(log_lines[-20:]), height=300, key="log_area")
else:
    st.warning("Log file is empty.")
