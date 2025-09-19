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
    initial_sidebar_state="expanded"
)

# Professional sidebar styling
st.markdown("""
<style>
/* Sidebar styling */
.css-1d391kg {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-right: 2px solid #e2e8f0;
}

/* Navigation buttons */
.stButton > button {
    width: 100%;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    text-align: left;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    border-color: #667eea;
    background: #f8fafc;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

/* Main header */
.main-header {
    text-align: center;
    color: #1a202c;
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin: 1rem 0;
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: #667eea;
}

.status-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-success { background-color: #10b981; }
.status-error { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("# 🚀 Universal RAG System")
    st.markdown("### Navigation")
    
    if st.button("💬 Chat Interface", help="Chat with your document collections"):
        st.switch_page("pages/01_chat.py")
    
    if st.button("➕ Create RAG Collection", help="Convert document folders to RAG collections"):
        st.switch_page("pages/02_create_rag_folder.py")
    
    if st.button("📊 Database Statistics", help="View database analytics and statistics"):
        st.switch_page("pages/03_database_stats.py")
    
    st.markdown("---")
    
    # System Status
    st.markdown("### System Status")
    
    # Check Ollama status
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            st.markdown('<span class="status-indicator status-success"></span>Ollama: Online', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-error"></span>Ollama: Error', unsafe_allow_html=True)
    except:
        st.markdown('<span class="status-indicator status-error"></span>Ollama: Offline', unsafe_allow_html=True)
    
    # Database status
    persist_dir = Path(os.getenv("PERSISTENT_DIR", "./persist"))
    if persist_dir.exists():
        st.markdown('<span class="status-indicator status-success"></span>Database: Ready', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-indicator status-error"></span>Database: Not Found', unsafe_allow_html=True)

# Main Content
st.markdown('<h1 class="main-header">Universal RAG System</h1>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 1.2rem; margin-bottom: 3rem;">
    Transform your documents into intelligent, searchable knowledge bases
</div>
""", unsafe_allow_html=True)

# Feature Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">💬</div>
        <h3 style="text-align: center; color: #1a202c;">Chat Interface</h3>
        <p style="color: #64748b; text-align: center;">
            Engage in intelligent conversations with your document collections using advanced AI models.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Start Chatting", key="start_chat", type="primary"):
        st.switch_page("pages/01_chat.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">➕</div>
        <h3 style="text-align: center; color: #1a202c;">Create Collections</h3>
        <p style="color: #64748b; text-align: center;">
            Convert your document folders into searchable RAG collections with custom AI models.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Create Collection", key="start_create", type="primary"):
        st.switch_page("pages/02_create_rag_folder.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">📊</div>
        <h3 style="text-align: center; color: #1a202c;">Database Analytics</h3>
        <p style="color: #64748b; text-align: center;">
            Monitor your collections, view statistics, and manage your knowledge base.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Analytics", key="start_stats", type="primary"):
        st.switch_page("pages/03_database_stats.py")

# Footer
st.markdown("""
---
<div style="text-align: center; color: #94a3b8; padding: 2rem;">
    <strong>Universal RAG System</strong> • Built with Streamlit, Ollama & ChromaDB<br>
    <small>Transform your documents into intelligent knowledge bases</small>
</div>
""", unsafe_allow_html=True)
