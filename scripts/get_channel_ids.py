import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_channel_id(channel_name):
    """Searches for a YouTube channel by name and returns its ID and Title."""
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY not found in .env file.")
        return None

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    try:
        search_response = youtube.search().list(
            q=channel_name,
            type="channel",
            part="id,snippet",
            maxResults=1
        ).execute()
        
        if not search_response.get('items'):
            return None

        item = search_response['items'][0]
        return {
            "title": item['snippet']['title'],
            "id": item['id']['channelId'],
            "description": item['snippet']['description']
        }
        
    except Exception as e:
        print(f"Error searching for {channel_name}: {e}")
        return None

def main():
    if len(sys.argv) > 1:
        channel_names = sys.argv[1:]
    else:
        print("Enter YouTube channel names (comma-separated):")
        user_input = input().strip()
        if not user_input:
            print("No input provided.")
            return
        channel_names = [name.strip() for name in user_input.split(',')]

    print(f"\nSearching for {len(channel_names)} channels...\n")
    print(f"{'Channel Name':<30} | {'Channel ID':<25} | {'Description'}")
    print("-" * 80)

    for name in channel_names:
        result = get_channel_id(name)
        if result:
            # Truncate description for display
            desc = result['description'][:20] + "..." if len(result['description']) > 20 else result['description']
            print(f"{result['title']:<30} | {result['id']:<25} | {desc}")
        else:
            print(f"{name:<30} | {'NOT FOUND':<25} | -")

if __name__ == "__main__":
    main()
