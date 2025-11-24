
import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import concurrent.futures

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env file")

# Date range: Last 60 days
END_DATE = datetime.now(timezone.utc)
START_DATE = END_DATE - timedelta(days=60)

# YouTube Channel IDs for Indian Tech News
CHANNEL_IDS = [
    # "UC62IIU805a_i4w_d9N_AN4g",  # Trakin Tech
    # "UCg3m_v-X_j1a_G-s_n2i4SA",  # Technical Guruji
    # "UCX-r7v_GA3u5e4g_LzE5T3w",  # Tech Burner
    # "UC7G6-z_p_3nB1vUv-K33jHw",  # C4ETech
    "UCO2WJZKQoDW4Te6NHx4KfTg",  # Geekyranjit
    "UCdp6GUwjKscp5ST4M4WgIpw",
    "UCsQoiOrh7jzKmE8NBofhTnQ",
    "UCA295QVkf9O1RQ8_-s3FVXg",
    "UCcPI9kEPhyUDLBHGOhKqxOw",
    "UCjQPoEg_RrJdFXarMhrwnfA",
    "UCnpekFV93kB1O0rVqEKSumg",
    # "UCOhVVPvj2tA3M4z4i2s0-2w",  # Beebom
    # "UCv65l3a3YU11i_2-2v3q5vA",  # Gogi Tech
    # "UCm-m7z763rS2S_Ea_S5A42n",  # Sharmaji Technical
    # "UCb0bEa_E22p4-G1e1a-A-2A",  # Prasadtechintelugu
]
OUTPUT_FILE = "indian_tech_videos.json"

# --- INITIALIZE CLIENT ---
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_all_videos_from_channels():
    """Fetches all video metadata from the specified YouTube channels."""
    print("Fetching video metadata from YouTube API...")
    all_videos = []
    
    for channel_id in CHANNEL_IDS:
        print(f"Fetching videos for channel: {channel_id}")
        
        # First, get the uploads playlist ID
        try:
            channel_response = youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Now fetch videos from the uploads playlist
            next_page_token = None
            while True:
                playlist_response = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                
                # Filter by date
                for item in playlist_response.get('items', []):
                    published_at = datetime.strptime(
                        item['snippet']['publishedAt'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    ).replace(tzinfo=timezone.utc)
                    
                    if START_DATE <= published_at <= END_DATE:
                        all_videos.append(item)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except Exception as e:
            print(f"An error occurred for channel {channel_id}: {e}")
            
    print(f"Found a total of {len(all_videos)} videos.")
    return all_videos
def fetch_transcript_and_details(video_item):
    """Fetches the transcript and full details for a single video."""
    # Try to get video ID from resourceId (playlistItem) or id (search result)
    video_id = video_item.get("snippet", {}).get("resourceId", {}).get("videoId")
    if not video_id:
        video_id = video_item.get("id", {}).get("videoId")
    
    if not video_id:
        return None

    try:
        # Get transcript
        # Note: The installed version of youtube_transcript_api requires instantiation
        # and uses .fetch() instead of .get_transcript()
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # transcript.snippets is a list of FetchedTranscriptSnippet objects
        transcript_text = " ".join([snippet.text for snippet in transcript.snippets])

        # Get video details
        snippet = video_item.get("snippet", {})
        
        return {
            "video_id": video_id,
            "title": snippet.get("title"),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": snippet.get("publishedAt"),
            "full_content": transcript_text,
            "source_type": "video"
        }
    except Exception as e:
        print(f"Could not get transcript for video ID {video_id}: {e}")
        return None

def main():
    """Main function to fetch, transcribe, and save videos."""
    video_items = get_all_videos_from_channels()
    
    if not video_items:
        print("No videos found. Exiting.")
        return

    transcribed_data = []
    print(f"\nFetching transcripts for {len(video_items)} videos using multiple threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_video = {executor.submit(fetch_transcript_and_details, item): item for item in video_items}
        for future in concurrent.futures.as_completed(future_to_video):
            result = future.result()
            if result:
                transcribed_data.append(result)
                print(f"Successfully transcribed: {result['title'][:50]}...")

    # Save to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(transcribed_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully saved {len(transcribed_data)} videos to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
