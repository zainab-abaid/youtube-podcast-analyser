import streamlit as st
import requests
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

# Import validation utilities
from url_validator import validate_youtube_url, extract_clean_url, get_validation_help_message

# Configure page
st.set_page_config(
    page_title="YouTube Podcast Analyzer",
    page_icon="🎙️",
    layout="centered"
)

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:12345")
# External URL for browser downloads (always localhost for user's browser)
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "http://localhost:12345")

# Initialize session state
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'download_url' not in st.session_state:
    st.session_state.download_url = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'last_url' not in st.session_state:
    st.session_state.last_url = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'show_existing_task_message' not in st.session_state:
    st.session_state.show_existing_task_message = None
if 'existing_task_status' not in st.session_state:
    st.session_state.existing_task_status = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'selected_user_filter' not in st.session_state:
    st.session_state.selected_user_filter = "All Users"

# Title
st.title("🎙️ YouTube Podcast Analyzer")
st.caption("*Optimized for GenAI related podcasts*")

# Auto-refresh settings
col1, col2 = st.columns([4, 1])

# Function to check if any tasks are processing
def has_active_tasks():
    try:
        response = requests.get(f"{API_BASE_URL}/api/tasks")
        if response.status_code == 200:
            tasks = response.json()
            for task_id, task_data in tasks.items():
                if task_data.get("status") in ["processing", "queued"]:
                    return True
        return False
    except:
        return False

# Function to fetch and display tasks table
def display_tasks_table():
    # Create a placeholder for the table
    table_container = st.container()
    
    with table_container:
        try:
            response = requests.get(f"{API_BASE_URL}/api/tasks")
            if response.status_code == 200:
                tasks = response.json()
                
                if tasks:
                    # Create header row with filter
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.subheader("Tasks")
                    
                    # Get unique users for filter dropdown
                    unique_users = set()
                    for task_data in tasks.values():
                        username = task_data.get("username", "")
                        unique_users.add(username if username else "N/A")
                    
                    # Sort users and add "All Users" option
                    user_options = ["All Users"] + sorted(list(unique_users))
                    
                    with col2:
                        selected_user = st.selectbox(
                            "Filter by User",
                            options=user_options,
                            index=0,
                            key="user_filter",
                            label_visibility="collapsed"
                        )
                        st.session_state.selected_user_filter = selected_user
                    
                    # Filter tasks for in-progress, completed, and error
                    filtered_tasks = []
                    for task_id, task_data in tasks.items():
                        if task_data.get("status") in ["processing", "queued", "completed", "error"]:
                            task_username = task_data.get("username", "")
                            display_username = task_username if task_username else "N/A"
                            
                            # Apply user filter
                            if selected_user != "All Users" and display_username != selected_user:
                                continue
                            
                            filtered_tasks.append({
                                "task_id": task_id,
                                "video_name": task_data.get("youtube_video_name", "Unknown"),
                                "username": display_username,
                                "status": task_data.get("status", "unknown").title(),
                                "youtube_url": task_data.get("youtube_url", ""),
                                "error": task_data.get("error", "")
                            })
                    
                    if filtered_tasks:
                        # Minimal table styling
                        st.markdown("""
                        <style>
                        .minimal-table {
                            width: 100%;
                            margin: 1rem 0;
                        }
                        .minimal-table-header {
                            font-size: 0.85rem;
                            font-weight: 500;
                            color: #6b7280;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            padding-bottom: 0.5rem;
                            border-bottom: 1px solid #e5e7eb;
                            margin-bottom: 0.75rem;
                        }
                        .minimal-table-row {
                            padding: 0.75rem 0;
                            border-bottom: 1px solid #f3f4f6;
                            display: flex;
                            align-items: center;
                        }
                        .minimal-table-row:last-child {
                            border-bottom: none;
                        }
                        /* Universal video name styling that works in both themes */
                        .video-name {
                            font-size: 0.9rem;
                            color: #4b5563 !important;
                            line-height: 1.4;
                        }
                        .username-text {
                            font-size: 0.85rem;
                            color: #6b7280;
                            font-style: italic;
                        }
                        .status-text {
                            font-size: 0.85rem;
                            color: #6b7280;
                        }
                        .status-processing {
                            color: #f59e0b;
                        }
                        .status-completed {
                            color: #10b981;
                        }
                        .status-queued {
                            color: #6366f1;
                        }
                        .status-error {
                            color: #ef4444;
                        }
                        /* Style retry buttons to look like action links */
                        .stButton > button {
                            background: none !important;
                            border: none !important;
                            color: #6b7280 !important;
                            font-size: 1.3rem !important;
                            padding: 0 !important;
                            margin: 0 auto !important;
                            transition: color 0.2s !important;
                            box-shadow: none !important;
                            width: auto !important;
                            height: auto !important;
                            display: block !important;
                        }
                        .stButton > button:hover {
                            color: #374151 !important;
                            background: none !important;
                            border: none !important;
                        }
                        .stButton > button:focus {
                            outline: none !important;
                            box-shadow: none !important;
                            border: none !important;
                        }
                        .stButton {
                            display: flex !important;
                            justify-content: center !important;
                            align-items: center !important;
                        }
                        .action-link {
                            color: #6b7280;
                            text-decoration: none;
                            font-size: 1.3rem;
                            transition: color 0.2s;
                        }
                        .action-link:hover {
                            color: #374151;
                        }
                        .minimal-table-cell {
                            display: flex;
                            align-items: center;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Table container
                        st.markdown('<div class="minimal-table">', unsafe_allow_html=True)
                        
                        # Table headers
                        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                        with col1:
                            st.markdown('<div class="minimal-table-header">Video</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown('<div class="minimal-table-header">User</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown('<div class="minimal-table-header">Status</div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown('<div class="minimal-table-header" style="text-align: center;">Action</div>', unsafe_allow_html=True)
                        
                        # Display table rows
                        for task in filtered_tasks:
                            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                            
                            with col1:
                                # Truncate long video names
                                video_name = task["video_name"]
                                if len(video_name) > 40:
                                    video_name = video_name[:37] + "..."
                                st.markdown(f'<div class="video-name">{video_name}</div>', unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f'<div class="username-text">{task["username"]}</div>', unsafe_allow_html=True)
                            
                            with col3:
                                status = task["status"].lower()
                                if status == "processing":
                                    st.markdown('<span class="status-text status-processing">🔄 Processing</span>', unsafe_allow_html=True)
                                elif status == "queued":
                                    st.markdown('<span class="status-text status-queued">⏳ Queued</span>', unsafe_allow_html=True)
                                elif status == "completed":
                                    st.markdown('<span class="status-text status-completed">✅ Completed</span>', unsafe_allow_html=True)
                                elif status == "error":
                                    st.markdown('<span class="status-text status-error">❌ Error</span>', unsafe_allow_html=True)
                            
                            with col4:
                                if task["status"] == "Completed":
                                    download_url = f"{EXTERNAL_API_URL}/api/download/{task['task_id']}"
                                    st.markdown(f'<div style="text-align: center;"><a href="{download_url}" class="action-link" target="_blank" title="Download">📥</a></div>', unsafe_allow_html=True)
                                elif task["status"] == "Error":
                                    # Simple retry button that looks exactly like download button
                                    retry_key = f"retry_{task['task_id']}"
                                    if st.button("🔄", key=retry_key, help="Retry processing this video"):
                                        # Retry the task
                                        try:
                                            retry_response = requests.post(
                                                f"{API_BASE_URL}/api/process",
                                                params={
                                                    "youtube_url": task["youtube_url"],
                                                    "username": task.get("username", "")
                                                }
                                            )
                                            if retry_response.status_code == 200:
                                                st.success("✅ Task restarted successfully!")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to restart task: {retry_response.text}")
                                        except Exception as e:
                                            st.error(f"❌ Error restarting task: {str(e)}")
                                else:
                                    st.markdown('<div style="text-align: center; color: #d1d5db;">—</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No active tasks found.")
                else:
                    st.info("No tasks found.")
        except Exception as e:
            st.error(f"Error fetching tasks: {str(e)}")

# Show existing task notification if present
if st.session_state.show_existing_task_message:
    if st.session_state.existing_task_status == "completed":
        # Show success message with download button
        success_container = st.container()
        with success_container:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success("✅ This video has already been processed!")
            with col2:
                if st.session_state.task_id:
                    download_url = f"{EXTERNAL_API_URL}/api/download/{st.session_state.task_id}"
                    st.link_button(
                        "📥 Download",
                        download_url,
                        type="primary",
                        use_container_width=True
                    )
    elif st.session_state.existing_task_status == "processing":
        st.warning("⏳ This video is currently being processed. Check the status in the table below.")
    elif st.session_state.existing_task_status == "queued":
        st.info("📋 This video is queued for processing. It will start soon.")
    
    # Clear the message after showing it
    st.session_state.show_existing_task_message = None

# Form container with proper state management
form_container = st.container()
with form_container:
    with st.form("youtube_form", clear_on_submit=False):
        # Username input
        username = st.text_input(
            "Username (optional)",
            placeholder="Enter your username",
            help="Enter your username to track your video processing tasks. Leave blank if you prefer to remain anonymous.",
            key="username_input",
            value=st.session_state.username
        )
        
        # YouTube URL input with helper text
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
            help="Enter a YouTube video URL. Supported formats: youtube.com/watch?v=..., youtu.be/..., or m.youtube.com/watch?v=...",
            key="url_input"
        )
        
        # Submit button
        submit_button = st.form_submit_button(
            "Generate Summary",
            use_container_width=True,
            type="primary"
        )

# Process the form submission
if submit_button:
    # Save username to session state
    st.session_state.username = username
    
    # Validate the YouTube URL
    is_valid, error_msg, video_id = validate_youtube_url(youtube_url)
    
    if not is_valid:
        st.error(f"❌ {error_msg}")
        
        # Provide helpful suggestions based on the error
        help_msg = get_validation_help_message(error_msg)
        if help_msg:
            st.info(help_msg)
    else:
        # Clean the URL before processing
        clean_url = extract_clean_url(youtube_url)
        st.session_state.error_message = None
        # Save URL for retry
        st.session_state.last_url = clean_url
        
        # Start processing
        try:
            # Call the API with the clean URL and username
            response = requests.post(
                f"{API_BASE_URL}/api/process",
                params={
                    "youtube_url": clean_url,
                    "username": username
                }
            )
            if response.status_code == 200:
                result = response.json()
                st.session_state.task_id = result["task_id"]
                st.session_state.error_message = None
                st.session_state.form_submitted = True
                
                # Check if this is an existing task
                if result["status"].startswith("existing_task_"):
                    actual_status = result["status"].replace("existing_task_", "")
                    
                    # Set flags for showing appropriate message
                    st.session_state.show_existing_task_message = True
                    st.session_state.existing_task_status = actual_status
                    
                    if actual_status == "completed":
                        # Task is already completed
                        st.session_state.download_url = result.get("download_url", f"{EXTERNAL_API_URL}/api/download/{result['task_id']}")
                        st.session_state.processing = False
                    else:
                        # Task is still processing or queued
                        st.session_state.processing = True
                        st.session_state.download_url = None
                else:
                    # New task
                    st.session_state.processing = True
                    st.session_state.download_url = None
                    st.session_state.show_existing_task_message = None
                    st.session_state.existing_task_status = None
                
                # Use st.rerun() with a small delay to prevent form duplication
                time.sleep(0.1)
                st.rerun()
            else:
                # Check if it's a specific API error
                if response.status_code == 400:
                    st.error(f"❌ API rejected the URL: {response.text}")
                elif response.status_code == 404:
                    st.error(f"❌ Video not found or unavailable. Please check if the video is public and accessible.")
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the API server. Please make sure the backend is running on port 12345.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")


# Display tasks table
display_tasks_table()

# Processing status check
if st.session_state.processing and st.session_state.task_id:
    # Show processing message
    st.info("🔄 Your video is being processed. You can see the progress in the table above.")
    
    # Add a progress indicator
    progress_container = st.container()
    with progress_container:
        with st.spinner("Processing..."):
            # Check status in background without blocking UI
            try:
                status_response = requests.get(
                    f"{API_BASE_URL}/api/status/{st.session_state.task_id}"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    # Handle both regular and existing_task_ status formats
                    actual_status = status_data["status"]
                    if actual_status.startswith("existing_task_"):
                        actual_status = actual_status.replace("existing_task_", "")
                    
                    if actual_status == "completed":
                        # Stop processing flag since task is done
                        st.session_state.processing = False
                        st.session_state.download_url = f"{EXTERNAL_API_URL}/api/download/{st.session_state.task_id}"
                        st.rerun()
                        
                    elif actual_status == "error":
                        # Save error and stop processing
                        st.session_state.error_message = status_data.get('error', 'Unknown error occurred')
                        st.session_state.processing = False
                        st.rerun()
                        
            except Exception as e:
                # Don't show connection errors during processing, just continue
                pass

# Show error if failed
if st.session_state.error_message and not st.session_state.processing:
    st.error(f"❌ Processing failed: {st.session_state.error_message}")

# Check if there are any active tasks
if has_active_tasks() or st.session_state.processing:
    # Auto-refresh every 3 seconds
    time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
    if time_since_refresh > 3:
        st.session_state.last_refresh = datetime.now()
        time.sleep(0.1)  # Small delay to prevent too rapid refreshing
        st.rerun()
    else:
        # Schedule next refresh
        remaining_time = 3 - time_since_refresh
        with st.empty():
            time.sleep(remaining_time)
            st.rerun()