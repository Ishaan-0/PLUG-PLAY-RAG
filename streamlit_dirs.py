import streamlit as st
import os
import platform
from pathlib import Path
from datetime import datetime
import humanize


# Set page config
st.set_page_config(
    page_title="File Explorer",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_system_roots():
    """Get all root directories for the current system"""
    system = platform.system()
    
    if system == "Windows":
        import string
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            try:
                if os.path.exists(drive):
                    drives.append(drive)
            except Exception:
                # Ignore errors in checking drive existence
                pass
        return drives
    else:
        return ['/']


def get_file_info(file_path):
    """Get file information including size and modification date"""
    try:
        stat = os.stat(file_path)
        size = humanize.naturalsize(stat.st_size)
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return size, modified
    except (OSError, FileNotFoundError):
        return "Unknown", "Unknown"


def get_folder_icon(is_expanded=False):
    """Get folder icon based on expansion state"""
    return "📂" if is_expanded else "📁"


def get_file_icon(filename):
    """Get file icon based on file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    icon_map = {
        '.txt': '📄', '.md': '📝', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
        '.xls': '📊', '.xlsx': '📊', '.csv': '📊', '.py': '🐍', '.js': '📜',
        '.html': '🌐', '.css': '🎨', '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️',
        '.gif': '🖼️', '.svg': '🖼️', '.mp4': '🎥', '.avi': '🎥', '.mov': '🎥',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.zip': '🗜️', '.rar': '🗜️',
        '.7z': '🗜️', '.tar': '🗜️', '.gz': '🗜️', '.json': '📋', '.xml': '📋',
        '.exe': '⚙️', '.app': '⚙️', '.dmg': '💿', '.iso': '💿'
    }
    
    return icon_map.get(ext, '📄')


def filter_items(items, show_hidden=False):
    """Filter items based on hidden file settings"""
    if not show_hidden:
        return [item for item in items if not item.startswith('.')]
    return items


def render_file_tree(path, max_depth=3, current_depth=0, key_prefix="", show_hidden=False):
    """Render file tree recursively using Streamlit components"""
    
    # Fixed: Use >= instead of > to prevent going beyond max_depth
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(path))
        # Apply hidden file filtering
        items = filter_items(items, show_hidden)
        
        folders = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]
        
        # Display folders first
        for idx, folder in enumerate(folders):
            folder_path = os.path.join(path, folder)
            # Improved key generation to avoid conflicts
            folder_key = f"{key_prefix}_{current_depth}_{idx}_{folder}"
            
            try:
                # Create expandable container for folders
                with st.expander(f"{get_folder_icon()} {folder}", expanded=False):
                    render_file_tree(folder_path, max_depth, current_depth + 1, folder_key, show_hidden)
            except PermissionError:
                st.write(f"🔒 {folder} (Permission Denied)")
            except Exception as e:
                st.write(f"❌ {folder} (Error: {str(e)[:50]}...)")
        
        # Display files
        if files and current_depth < max_depth:
            st.write("**Files:**")
            
            # Create columns for file display
            for i in range(0, len(files), 3):  # Display 3 files per row
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(files):
                        file = files[i + j]
                        file_path = os.path.join(path, file)
                        size, modified = get_file_info(file_path)
                        
                        with col:
                            st.write(f"{get_file_icon(file)} **{file}**")
                            st.caption(f"Size: {size}")
                            st.caption(f"Modified: {modified}")
                            
                            # Fixed: Direct download button instead of conditional
                            try:
                                with open(file_path, 'rb') as f:
                                    file_data = f.read()
                                    st.download_button(
                                        label="📥 Download",
                                        data=file_data,
                                        file_name=file,
                                        key=f"dl_{current_depth}_{i}_{j}_{hash(file_path)}",
                                        help=f"Download {file}",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.caption(f"⚠️ Cannot download: {str(e)[:30]}...")
            
    except PermissionError:
        st.error("🔒 Permission denied to access this directory")
    except Exception as e:
        st.error(f"❌ Error accessing directory: {str(e)}")


def render_breadcrumb_navigation(current_path):
    """Render breadcrumb navigation with improved path handling"""
    try:
        path_obj = Path(current_path)
        path_parts = path_obj.parts
        breadcrumbs = []
        system = platform.system()
        
        # Reconstruct paths properly based on system
        for i, part in enumerate(path_parts):
            if system == "Windows":
                # Handle Windows paths correctly
                if i == 0:
                    # Drive letter with backslash
                    partial_path = part
                    if not part.endswith("\\"):
                        partial_path += "\\"
                else:
                    # Build full path from drive onwards
                    partial_path = str(Path(*path_parts[:i+1]))
            else:
                # Unix-like systems
                partial_path = "/" + "/".join(path_parts[1:i+1]) if i > 0 else "/"
            
            display_name = part if part else "Root"
            breadcrumbs.append((display_name, partial_path))
        
        # Display breadcrumbs with proper column handling
        if breadcrumbs:
            num_cols = min(len(breadcrumbs) + 1, 8)  # Limit columns to prevent overflow
            cols = st.columns(num_cols)
            
            for i, (name, path) in enumerate(breadcrumbs):
                if i < len(cols) - 1:  # Leave space for Home button
                    with cols[i]:
                        if st.button(f"📁 {name[:10]}...", key=f"breadcrumb_{i}", 
                                   help=f"Navigate to {path}"):
                            if os.path.exists(path) and os.path.isdir(path):
                                st.session_state.current_path = path
                                st.rerun()
            
            # Home button in last column
            with cols[-1]:
                if st.button("🏠 Home", key="breadcrumb_home"):
                    st.session_state.current_path = os.path.expanduser("~")
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error in breadcrumb navigation: {str(e)}")


def validate_path(path):
    """Validate if a path exists and is a directory"""
    try:
        return os.path.exists(path) and os.path.isdir(path)
    except Exception:
        return False


def main():
    st.title("🗂️ File Explorer")
    st.markdown("---")
    
    # Initialize session state with better error handling
    if 'current_path' not in st.session_state:
        try:
            roots = get_system_roots()
            default_path = roots[0] if roots else os.path.expanduser("~")
            st.session_state.current_path = default_path
        except Exception:
            st.session_state.current_path = os.path.expanduser("~")
    
    # Sidebar for quick navigation
    with st.sidebar:
        st.header("Quick Navigation")
        
        # System roots
        st.subheader("📀 System Drives")
        try:
            roots = get_system_roots()
            for root in roots:
                if st.button(f"💾 {root}", key=f"root_{root.replace(':', '_').replace('\\', '_')}"):
                    st.session_state.current_path = root
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading drives: {str(e)}")
        
        st.markdown("---")
        
        # Common directories
        st.subheader("📂 Quick Access")
        quick_paths = {
            "🏠 Home": os.path.expanduser("~"),
            "📋 Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "📥 Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "📄 Documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "🖼️ Pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "🎵 Music": os.path.join(os.path.expanduser("~"), "Music"),
            "🎥 Videos": os.path.join(os.path.expanduser("~"), "Videos"),
        }
        
        for name, path in quick_paths.items():
            if os.path.exists(path):
                if st.button(name, key=f"quick_{name.replace(' ', '_')}"):
                    st.session_state.current_path = path
                    st.rerun()
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Settings")
        max_depth = st.slider("Maximum folder depth", 1, 5, 3)
        show_hidden = st.checkbox("Show hidden files", False)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Path input with validation
        new_path = st.text_input(
            "📍 Current Path:", 
            value=st.session_state.current_path,
            key="path_input"
        )
        
        # Fixed: Added directory validation
        if new_path != st.session_state.current_path:
            if validate_path(new_path):
                st.session_state.current_path = new_path
                st.rerun()
            elif new_path.strip():  # Only show error if user entered something
                st.error(f"Invalid path or not a directory: {new_path}")
    
    with col2:
        if st.button("🔄 Refresh", key="refresh"):
            st.rerun()
        
        if st.button("⬆️ Parent", key="parent"):
            current = st.session_state.current_path
            parent = os.path.dirname(current)
            # Prevent infinite loop on root directories
            if parent != current and validate_path(parent):
                st.session_state.current_path = parent
                st.rerun()
    
    # Breadcrumb navigation
    render_breadcrumb_navigation(st.session_state.current_path)
    
    st.markdown("---")
    
    # Display current directory info
    try:
        if not validate_path(st.session_state.current_path):
            st.error(f"Invalid current path: {st.session_state.current_path}")
            # Reset to home directory
            st.session_state.current_path = os.path.expanduser("~")
            st.rerun()
            
        items = os.listdir(st.session_state.current_path)
        
        # Apply hidden file filtering
        items = filter_items(items, show_hidden)
        
        folders = [item for item in items if os.path.isdir(os.path.join(st.session_state.current_path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(st.session_state.current_path, item))]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Folders", len(folders))
        with col2:
            st.metric("📄 Files", len(files))
        with col3:
            st.metric("📊 Total Items", len(items))
        
        st.markdown("---")
        
        # Render the file tree
        render_file_tree(st.session_state.current_path, max_depth, show_hidden=show_hidden)
        
    except PermissionError:
        st.error("🔒 Permission denied to access this directory")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        # Reset to a safe path on error
        st.session_state.current_path = os.path.expanduser("~")
    
    # Footer
    st.markdown("---")
    st.caption("💡 Click on folders to expand/collapse • Use sidebar for quick navigation • Click breadcrumbs to navigate")


if __name__ == "__main__":
    main()
