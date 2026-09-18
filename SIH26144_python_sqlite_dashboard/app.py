import streamlit as st
from core.ui import inject_css
from core.runtime import init_state, restart_demo

import streamlit.components.v1 as components
#new_start

components.html(
    """
    <script>
    function hideAllBranding() {
        // Collect all accessible window levels (top window + parent window)
        const docs = [];
        try { if (window.top && window.top.document) docs.push(window.top.document); } catch(e) {}
        try { if (window.parent && window.parent.document) docs.push(window.parent.document); } catch(e) {}
        try { if (window.document) docs.push(window.document); } catch(e) {}

        docs.forEach(doc => {
            // 1. Inject aggressive CSS rule into the head of each document
            if (!doc.getElementById('custom-hide-style')) {
                const style = doc.createElement('style');
                style.id = 'custom-hide-style';
                style.innerHTML = `
                    div[data-testid="stViewerBadge"],
                    div[class*="viewerBadge"],
                    div[class*="ViewerBadge"],
                    div[class*="ProfileBadge"],
                    div[class*="toolbar"],
                    footer,
                    #MainMenu,
                    a[href*="github.com/esha-patel-13"],
                    a[href*="streamlit.io"] {
                        display: none !important;
                        opacity: 0 !important;
                        visibility: hidden !important;
                        pointer-events: none !important;
                    }
                `;
                doc.head.appendChild(style);
            }

            // 2. Search and remove all elements containing the badge text or github link
            const allElements = doc.querySelectorAll('div, a, span, p, footer, button');
            allElements.forEach(el => {
                const text = el.innerText || el.textContent || '';
                const href = el.getAttribute('href') || '';
                if (
                    text.includes('Created by') || 
                    text.includes('Hosted with Streamlit') || 
                    text.includes('esha-patel-13') ||
                    href.includes('esha-patel-13') ||
                    href.includes('streamlit.app')
                ) {
                    el.style.setProperty('display', 'none', 'important');
                    if (el.parentElement) {
                        el.parentElement.style.setProperty('display', 'none', 'important');
                    }
                }
            });

            // 3. Fallback: Place a matching dark cover-up box directly over the bottom-right corner
            if (!doc.getElementById('badge-cover-box')) {
                const cover = doc.createElement('div');
                cover.id = 'badge-cover-box';
                cover.style.cssText = `
                    position: fixed !important;
                    bottom: 0px !important;
                    right: 0px !important;
                    width: 320px !important;
                    height: 48px !important;
                    background-color: #0e1117 !important;
                    z-index: 999999999 !important;
                    pointer-events: none !important;
                `;
                doc.body.appendChild(cover);
            }
        });
    }

    // Run immediately and continuously monitor DOM changes
    hideAllBranding();
    setInterval(hideAllBranding, 300);

    try {
        const target = window.top.document.body || window.parent.document.body;
        const observer = new MutationObserver(hideAllBranding);
        observer.observe(target, { childList: true, subtree: true });
    } catch(e) {}
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


