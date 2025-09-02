import streamlit as st


st.set_page_config(page_title="Local RAG", layout="wide")

st.title("YOUR OWN LOCAL RAG")

# --- Initialize session state ---
if "folder_checked" not in st.session_state:
    st.session_state.folder_checked = False
if "folder_exists" not in st.session_state:
    st.session_state.folder_exists = False

# --- Sidebar: RAG System Control Panel ---
st.sidebar.header("RAG System Control Panel")

# 1️⃣ Step 1: Enter folder path
folder_path = st.sidebar.text_input("Enter folder path")

# Simulated check for folder existence in ChromaDB
def check_folder_exists(folder_path):
    # Replace this with your actual vector DB check
    existing_folders = ["data/folder1", "data/folder2"]
    return folder_path in existing_folders

# When user presses Enter in text box or clicks Check button
if folder_path and st.sidebar.button("Check Folder"):
    st.session_state.folder_checked = True
    st.session_state.folder_exists = check_folder_exists(folder_path)

# 2️⃣ Step 2: Conditional UI after checking folder
if st.session_state.folder_checked:
    if st.session_state.folder_exists:
        st.sidebar.success("This folder is already in internal knowledge. You can start chatting below!")
    else:
        st.sidebar.info("New folder detected. Configure your settings below:")
        
        # Embedding + LLM options shown only if folder doesn't exist
        embedding_choice = st.sidebar.selectbox("Choose Embedding Function", ["OpenAI", "HuggingFace", "InstructorXL"])
        llm_choice = st.sidebar.selectbox("Choose LLM", ["OpenAI GPT", "Llama2", "Local Model"])

        if st.sidebar.button("Process Folder"):
            st.sidebar.write(f"Processing folder: {folder_path}")
            # Call your actual processing function here
            # process_folder(folder_path, embedding_choice, llm_choice)
            st.success("Folder processed successfully! You can now chat with the model.")

# --- Main Chat UI Section ---
st.header("Chat with RAG")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat-like input at the bottom
user_query = st.chat_input("Ask a question...")

if user_query:
    with st.spinner("GENERATING RESPONSE..."):
        # Simulate LLM response
        response = f"Response to: {user_query}"  # Replace with retriever call
        st.session_state.chat_history.append(("You", user_query))
        st.session_state.chat_history.append(("Bot", response))

# Display chat in a nice markdown format
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Bot:** {message}")
