import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

st.set_page_config(
    page_title="Universal RAG System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark mode styling with consistent color palette
st.markdown("""
<style>
/* Hide default sidebar completely */
section[data-testid="stSidebar"] {
    display: none !important;
}

/* Global dark theme */
.stApp {
    background: #0f172a;
    color: #e2e8f0;
}

/* Hide default page navigation */
.css-10trblm, .css-16idsys {
    display: none !important;
}

/* Remove ALL white backgrounds from Streamlit components */
.main .block-container {
    background: transparent !important;
    padding-top: 2rem;
}

/* Column styling - remove white backgrounds */
div[data-testid="column"] {
    background: transparent !important;
}

div[data-testid="column"] > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    padding: 2rem !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="column"] > div:hover {
    background: #334155 !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.5) !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
}

/* Text styling */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
}

p {
    color: #cbd5e1 !important;
}

/* Status container styling */
.status-container {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin: 2rem 0 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
}

/* Status indicators */
.status-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    color: #e2e8f0;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 12px;
}

.status-success { background: #10b981; }
.status-error { background: #ef4444; }

/* Header styling */
.main-header {
    text-align: center;
    color: #f1f5f9;
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-shadow: 0 4px 8px rgba(0,0,0,0.5);
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 1.2rem;
    margin-bottom: 3rem;
}

/* Footer styling */
.footer {
    text-align: center;
    color: #64748b;
    margin-top: 3rem;
    padding: 2rem;
    border-top: 1px solid #334155;
}

/* Card content styling */
.card-content h3 {
    color: #f1f5f9 !important;
    margin-bottom: 1rem !important;
}

.card-content p {
    color: #94a3b8 !important;
    line-height: 1.6 !important;
    margin-bottom: 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Main content
st.markdown("""
<h1 class="main-header">Universal RAG System</h1>
<div class="subtitle">Transform your documents into intelligent, searchable knowledge bases</div>
""", unsafe_allow_html=True)

# Feature cards using Streamlit columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card-content">
        <h3>💬 Chat Interface</h3>
        <p>Engage in intelligent conversations with your document collections using advanced AI models.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Chatting", key="start_chat", type="primary"):
        st.switch_page("pages/01_chat.py")

with col2:
    st.markdown("""
    <div class="card-content">
        <h3>➕ Create Collections</h3>
        <p>Convert your document folders into searchable RAG collections with custom AI models.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Create Collection", key="start_create", type="primary"):
        st.switch_page("pages/02_create_rag_folder.py")

with col3:
    st.markdown("""
    <div class="card-content">
        <h3>📊 Database Analytics</h3>
        <p>Monitor your collections, view statistics, and manage your knowledge base.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Analytics", key="start_stats", type="primary"):
        st.switch_page("pages/03_database_stats.py")

# System Status
st.markdown("""
<div class="status-container">
    <h4 style="color: #f1f5f9; margin-bottom: 1rem;">System Status</h4>
""", unsafe_allow_html=True)

# Check Ollama status
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=3)
    if response.status_code == 200:
        st.markdown('<div class="status-item"><span class="status-dot status-success"></span>Ollama: Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-item"><span class="status-dot status-error"></span>Ollama: Error</div>', unsafe_allow_html=True)
except:
    st.markdown('<div class="status-item"><span class="status-dot status-error"></span>Ollama: Offline</div>', unsafe_allow_html=True)

# Database status
persist_dir = Path(os.getenv("PERSISTENT_DIR", ""))
if persist_dir.exists():
    st.markdown('<div class="status-item"><span class="status-dot status-success"></span>Database: Ready</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-item"><span class="status-dot status-error"></span>Database: Not Found</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <strong>Universal RAG System</strong> • Built with Streamlit, Ollama & ChromaDB<br>
    <small>Transform your documents into intelligent knowledge bases</small>
</div>
""", unsafe_allow_html=True)