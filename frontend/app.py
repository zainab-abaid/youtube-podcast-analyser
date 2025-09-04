import streamlit as st
import requests
import time
import os
from pathlib import Path

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

# Title
st.title("🎙️ YouTube Podcast Analyzer")
st.caption("*Optimized for GenAI related podcasts*")

# Only show form if not processing
if not st.session_state.processing:
    with st.form("youtube_form"):
        # YouTube URL input with helper text
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
            help="Enter a YouTube video URL. Supported formats: youtube.com/watch?v=..., youtu.be/..., or m.youtube.com/watch?v=..."
        )
        
        # Submit button
        submit_button = st.form_submit_button(
            "Generate Summary",
            use_container_width=True,
            type="primary"
        )

    # Process the form submission
    if submit_button:
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
            # Generate filename with timestamp
            output_filename = f"analysis_{int(time.time())}"
            
            # Show what we're processing
            st.success(f"✅ Valid YouTube URL detected (Video ID: {video_id})")
            
            # Start processing
            try:
                # Call the API with the clean URL
                response = requests.post(
                    f"{API_BASE_URL}/api/process",
                    params={
                        "youtube_url": clean_url,
                        "output_filename": output_filename
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.task_id = result["task_id"]
                    st.session_state.processing = True
                    st.session_state.download_url = None
                    st.session_state.error_message = None
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

# Processing or result display
if st.session_state.processing and st.session_state.task_id:
    # Create a placeholder for the processing message
    status_placeholder = st.empty()
    
    # Show processing animation
    with status_placeholder.container():
        with st.spinner("Processing your video... This may take a few minutes."):
            # Keep checking status until complete
            while st.session_state.processing:
                try:
                    status_response = requests.get(
                        f"{API_BASE_URL}/api/status/{st.session_state.task_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data["status"] == "completed":
                            # Save download URL and stop processing
                            st.session_state.download_url = f"{API_BASE_URL}/api/download/{st.session_state.task_id}"
                            st.session_state.processing = False
                            st.rerun()
                            
                        elif status_data["status"] == "error":
                            # Save error and stop processing
                            st.session_state.error_message = status_data.get('error', 'Unknown error occurred')
                            st.session_state.processing = False
                            st.rerun()
                        
                        # If still processing or queued, wait before next check
                        else:
                            time.sleep(3)
                            
                except Exception as e:
                    st.session_state.error_message = f"Connection error: {str(e)}"
                    st.session_state.processing = False
                    st.rerun()
                    break

# Show download section if successful - appears instantly!
elif st.session_state.download_url:
    
    # Simple CSS for minimal green button
    st.markdown("""
    <style>
    .minimal-download {
        text-align: center;
        margin: 0 0 2rem 0;
    }
    .minimal-download a {
        background-color: #4CAF50;
        color: white !important;
        padding: 0.5rem 1.5rem;
        border-radius: 0.25rem;
        text-decoration: none !important;
        font-size: 1rem;
        display: inline-block;
    }
    .minimal-download a:hover {
        background-color: #45a049;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Minimal download button
    st.markdown(f"""
    <div class="minimal-download">
        <a href="{st.session_state.download_url}" target="_blank">
            Download Results
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Analyze Another Video", use_container_width=True):
            # Reset state
            st.session_state.task_id = None
            st.session_state.processing = False
            st.session_state.download_url = None
            st.session_state.error_message = None
            st.rerun()
    
    with col2:
        if st.button("📋 Copy Download Link", use_container_width=True):
            # JavaScript to copy to clipboard
            st.components.v1.html(f"""
            <script>
                navigator.clipboard.writeText('{st.session_state.download_url}').then(function() {{
                    alert('Download link copied to clipboard!');
                }});
            </script>
            """, height=0)

# Show error if failed
elif st.session_state.error_message and not st.session_state.processing:
    st.error(f"❌ Processing failed: {st.session_state.error_message}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Retry", use_container_width=True, type="primary"):
            if st.session_state.last_url:
                st.session_state.error_message = None
                st.session_state.processing = True
                # Generate new filename with timestamp
                output_filename = f"analysis_{int(time.time())}"
                
                # Retry with the same URL
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/process",
                        params={
                            "youtube_url": st.session_state.last_url,
                            "output_filename": output_filename
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.task_id = result["task_id"]
                        st.session_state.processing = True
                        st.session_state.download_url = None
                        st.session_state.error_message = None
                        st.rerun()
                    else:
                        st.session_state.error_message = f"API Error {response.status_code}: {response.text}"
                        st.rerun()
                        
                except requests.exceptions.ConnectionError:
                    st.session_state.error_message = "Could not connect to the API server. Please make sure the backend is running on port 12345."
                    st.rerun()
                except Exception as e:
                    st.session_state.error_message = str(e)
                    st.rerun()
    
    with col2:
        if st.button("Start Over", use_container_width=True):
            # Reset all state
            st.session_state.task_id = None
            st.session_state.processing = False
            st.session_state.download_url = None
            st.session_state.error_message = None
            st.session_state.last_url = None
            st.rerun()