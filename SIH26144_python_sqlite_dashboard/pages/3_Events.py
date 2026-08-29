import pandas as pd
import streamlit as st
from core.ui import inject_css, header
from core.database import read_events
from core.config import DB_PATH

inject_css(); header()
st.markdown("## Event Log")
if st.session_state.get("event_log"):
    df=pd.DataFrame(list(reversed(st.session_state.event_log)))
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("Export runtime events",df.to_csv(index=False).encode(),"runtime_events.csv","text/csv")
else:
    st.info("No runtime detections recorded in this demonstration yet.")
st.markdown("## Recorded Events")
recorded=pd.DataFrame(list(reversed(read_events(DB_PATH,100))))
if recorded.empty: st.info("No recorded events in database.")
else:
    st.dataframe(recorded,use_container_width=True,hide_index=True)
    st.download_button("Export recorded events",recorded.to_csv(index=False).encode(),"microbarometer_events.csv","text/csv")
