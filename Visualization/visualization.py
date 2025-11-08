import streamlit as st
from ui.theme import inject_css

def app():
    inject_css()
    st.header(":material/monitoring: Dashboard")
    st.caption("High-level KPIs and quick links.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Projects", "7", "+2")
    k2.metric("On-time Deliverables", "92%", "↑")
    k3.metric("Model Accuracy", "0.86 F1", "↑")
    k4.metric("Citizen Reports (24h)", "134", "↓")
    st.divider()
    st.subheader("What’s new")
    st.write("- New EDA slice for mobility vs incident rate\n- ML retraining scheduled weekly\n- Citizen feedback form refreshed")

if __name__ == "__main__":
    app()
