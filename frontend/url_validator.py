"""
YouTube URL validation utilities for the Podcast Analyzer app.
"""

import re
from urllib.parse import urlparse, parse_qs


def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube video URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None, video_id: str or None)
    """
    if not url:
        return False, "Please enter a YouTube URL", None
    
    # Clean up the URL (remove whitespace)
    url = url.strip()
    
    # Check if it's a valid URL
    try:
        parsed_url = urlparse(url)
    except:
        return False, "Invalid URL format", None
    
    # Check if it has a scheme (http/https)
    if not parsed_url.scheme:
        return False, "URL must start with http:// or https://", None
    
    # Check if it's a YouTube domain
    valid_youtube_domains = [
        'youtube.com', 
        'www.youtube.com', 
        'm.youtube.com',
        'youtu.be',
        'www.youtu.be'
    ]
    
    domain = parsed_url.netloc.lower()
    if domain not in valid_youtube_domains:
        return False, "URL must be from YouTube (youtube.com or youtu.be)", None
    
    video_id = None
    
    # Extract video ID based on URL format
    if 'youtu.be' in domain:
        # Format: https://youtu.be/VIDEO_ID
        path = parsed_url.path
        if path and len(path) > 1:
            video_id = path[1:].split('?')[0].split('&')[0]
        else:
            return False, "Invalid YouTube short URL - no video ID found", None
    else:
        # Format: https://www.youtube.com/watch?v=VIDEO_ID
        # or: https://www.youtube.com/embed/VIDEO_ID
        # or: https://m.youtube.com/watch?v=VIDEO_ID
        
        if '/watch' in parsed_url.path:
            # Extract from query parameters
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params and query_params['v']:
                video_id = query_params['v'][0]
            else:
                return False, "No video ID found in YouTube URL", None
        elif '/embed/' in parsed_url.path:
            # Extract from path
            path_parts = parsed_url.path.split('/embed/')
            if len(path_parts) > 1:
                video_id = path_parts[1].split('?')[0].split('&')[0]
            else:
                return False, "Invalid YouTube embed URL", None
        elif '/v/' in parsed_url.path:
            # Old format: https://www.youtube.com/v/VIDEO_ID
            path_parts = parsed_url.path.split('/v/')
            if len(path_parts) > 1:
                video_id = path_parts[1].split('?')[0].split('&')[0]
            else:
                return False, "Invalid YouTube URL format", None
        else:
            return False, "Unsupported YouTube URL format. Please use a standard YouTube video URL", None
    
    # Validate video ID format (should be 11 characters, alphanumeric with - and _)
    if video_id:
        # YouTube video IDs are typically 11 characters
        if not re.match(r'^[a-zA-Z0-9_-]{10,12}$', video_id):
            return False, "Invalid YouTube video ID format", None
        return True, None, video_id
    else:
        return False, "Could not extract video ID from URL", None


def extract_clean_url(url):
    """
    Extract a clean YouTube URL from the input, removing extra parameters.
    
    Args:
        url (str): The YouTube URL to clean
        
    Returns:
        str: A clean YouTube URL with just the video ID, or the original URL if invalid
    """
    is_valid, error, video_id = validate_youtube_url(url)
    if is_valid and video_id:
        # Return a clean URL with just the video ID
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def get_validation_help_message(error_msg):
    """
    Get a helpful message based on the validation error.
    
    Args:
        error_msg (str): The error message from validation
        
    Returns:
        str or None: A helpful suggestion message
    """
    if not error_msg:
        return None
        
    error_lower = error_msg.lower()
    
    if "youtube.com or youtu.be" in error_lower:
        return ("💡 Make sure you're copying the URL from YouTube. It should look like:\n"
                "• https://www.youtube.com/watch?v=xxxxx\n"
                "• https://youtu.be/xxxxx")
    elif "http://" in error_lower:
        return "💡 Try adding https:// at the beginning of your URL"
    elif "video id" in error_lower:
        return "💡 Make sure you're copying the full YouTube video URL, not just the video page"
    
    return None