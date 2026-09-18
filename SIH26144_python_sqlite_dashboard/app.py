import streamlit as st
from core.ui import inject_css
from core.runtime import init_state, restart_demo

import streamlit.components.v1 as components
#new_start

# Inject JavaScript to reach into parent window and remove the Streamlit Cloud footer badge
components.html(
    """
    <script>
    function removeBadges() {
        try {
            const parentDoc = window.parent.document;
            
            // 1. Remove by Streamlit Cloud data-testids and classes
            const elements = parentDoc.querySelectorAll(
                'div[data-testid="stViewerBadge"], div[class*="viewerBadge"], [data-testid="stToolbar"], footer'
            );
            elements.forEach(el => el.style.setProperty('display', 'none', 'important'));
            
            // 2. Remove by text content ("Created by" / "Hosted with Streamlit")
            const allElements = parentDoc.querySelectorAll('div, a, span, p');
            allElements.forEach(el => {
                if (el.textContent && (el.textContent.includes('Created by') || el.textContent.includes('Hosted with Streamlit'))) {
                    el.style.setProperty('display', 'none', 'important');
                    if (el.parentElement) el.parentElement.style.setProperty('display', 'none', 'important');
                }
            });
        } catch (e) {
            console.log(e);
        }
    }

    // Run repeatedly to catch dynamic renders
    removeBadges();
    setInterval(removeBadges, 500);
    </script>
    """,
    height=0,
    width=0
)
#new_over

st.set_page_config(page_title="SIH26144 Microbarometer", page_icon=":material/air:", layout="wide", initial_sidebar_state="expanded")
inject_css()
init_state()

with st.sidebar:
    st.markdown("## SIH26144")
    if st.button("↻ Restart demonstration", use_container_width=True):
        restart_demo()
        st.rerun()

monitoring = st.Page("pages/1_Live_Dashboard.py", title="Live Dashboard", icon=":material/dashboard:", default=True)
analysis = st.Page("pages/2_Signal_Analysis.py", title="Signal Analysis", icon=":material/analytics:")
events = st.Page("pages/3_Events.py", title="Events", icon=":material/warning:")
system = st.Page("pages/4_System.py", title="System", icon=":material/settings:")
prototype = st.Page("pages/5_Prototype.py", title="Prototype", icon=":material/view_in_ar:")
about = st.Page("pages/6_About.py", title="About", icon=":material/info:")

pg = st.navigation([monitoring, analysis, events, system, prototype, about])
pg.run()


