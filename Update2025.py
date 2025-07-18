import streamlit as st
import requests
from datetime import datetime, timedelta
import re

# YouTube API Key
API_KEY = "AIzaSyClb1FgCWaiDpnhJAEY5pxLvCQwZAOpwIk"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# ===== CONFIGURATION PARAMETERS =====
# 1. MAX_SUBSCRIBERS: Set max allowed subscribers (currently 50,000)
MAX_SUBSCRIBERS = 50000

# 2. MAX_CHANNEL_AGE_MONTHS: Set max channel age in months (currently 6 months)
MAX_CHANNEL_AGE_MONTHS = 6
# ====================================

# List of broader keywords
keywords = [
 "Celebrity News", "Hollywood Gossip", "Celebrity Drama", "Celebrity Scandal",
 "Viral Celebrity Moments", "A-List Celebs", "Breaking Hollywood", "Hollywood Rumors",
 "Paparazzi Footage", "Celebrity Breakup", "Shocking Celeb Secrets", "Celeb Leaks",
 "Celebrity Exposed", "Celebrity Couples", "Secret Celebrity Affairs", "Celeb Cheating Rumors",
 "Red Carpet Moments", "Celeb Fashion Fails", "Celeb Fights Caught On Camera", "Ex Celebrity Secrets",
 "Celebrity Court Case", "Hollywood Legal Drama", "Celeb Arrest News", "Viral Celeb Clips",
 "Behind The Fame", "Hollywood Celeb Update", "Latest Celeb Tea", "Celeb Feud Explained",
 "Pop Culture Drama", "Celebrity Beef", "Star Caught Lying", "Famous Breakup Story",
 "TMZ Style Drama", "Celebrity Meltdown", "Hollywood Exposed", "Celebrity Love Triangle",
 "Scandalous Celebs", "Famous Divorce News", "Hidden Celeb Lives", "Reddit Celeb Gossip"
]

# Helper function to parse ISO 8601 duration
def parse_duration(duration_str):
    """Convert ISO 8601 duration to minutes"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    
    return hours * 60 + minutes + seconds / 60

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date ranges
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        # Calculate max channel age cutoff (6 months ago)
        max_channel_age = (datetime.utcnow() - timedelta(days=MAX_CHANNEL_AGE_MONTHS*30)).isoformat("T") + "Z"
        
        all_results = []

        # Iterate over the list of keywords
        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            # Define search parameters
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            # Check if "items" key exists
            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            # Fetch video statistics and duration
            stats_params = {
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel statistics AND creation date
            channel_params = {
                "part": "statistics,snippet",  # Added snippet to get channel creation date
                "id": ",".join(channel_ids),
                "key": API_KEY
            }
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                # Get and parse duration
                duration_str = stat["contentDetails"]["duration"]
                duration_minutes = parse_duration(duration_str)
                
                # Skip videos outside 4-20 minute range
                if not (4 <= duration_minutes <= 20):
                    continue
                    
                # Get channel creation date
                channel_creation = channel["snippet"]["publishedAt"]
                
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))
                created_date = datetime.strptime(channel_creation, "%Y-%m-%dT%H:%M:%SZ")

                # Apply new filters:
                # 1. Subs <= 50,000
                # 2. Channel created within last 8 months
                if subs <= MAX_SUBSCRIBERS and created_date >= datetime.strptime(max_channel_age, "%Y-%m-%dT%H:%M:%SZ"):
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "Duration (min)": round(duration_minutes, 1),
                        "Channel Created": created_date.strftime("%Y-%m-%d")
                    })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Duration:** {result['Duration (min)']} minutes  \n"
                    f"**Channel Created:** {result['Channel Created']}"  # Show creation date
                )
                st.write("---")
        else:
            st.warning(f"No results found for channels with ≤{MAX_SUBSCRIBERS:,} subscribers created within last {MAX_CHANNEL_AGE_MONTHS} months")

    except Exception as e:
        st.error(f"An error occurred: {e}")
