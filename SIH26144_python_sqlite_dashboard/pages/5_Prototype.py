from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from core.ui import inject_css, header

inject_css(); header()
st.markdown("## 3D Prototype")
prototype=(Path(__file__).parents[1]/"prototype.html").read_text(encoding="utf-8")
components.html(prototype,height=720,scrolling=False)
