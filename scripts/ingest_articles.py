
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from newsapi import NewsApiClient
from newspaper import Article
import concurrent.futures

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise ValueError("NEWS_API_KEY not found in .env file")

# Date range: Last 30 days
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=30)

# Query parameters
TECH_QUERY_STRING = "tech OR technology OR startup OR AI OR ML OR data science OR fintech"
INDIAN_SOURCES = "the-times-of-india,the-hindu,business-standard,financial-express,the-economic-times,livemint"
OUTPUT_FILE = "indian_tech_articles.json"

# --- INITIALIZE CLIENT ---
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def fetch_all_articles():
    """Fetches all article metadata from the NewsAPI."""
    print("Fetching article metadata from NewsAPI...")
    all_articles = []
    page = 1
    while True:
        try:
            response = newsapi.get_everything(
                q=TECH_QUERY_STRING,
                sources=INDIAN_SOURCES,
                from_param=START_DATE.strftime('%Y-%m-%d'),
                to=END_DATE.strftime('%Y-%m-%d'),
                language='en',
                sort_by='publishedAt',
                page=page
            )
            if not response['articles']:
                break
            all_articles.extend(response['articles'])
            print(f"Fetched page {page}, total articles so far: {len(all_articles)}")
            page += 1
            if page > 5: # API has a limit for developer accounts
                print("Reached page limit for developer account.")
                break
        except Exception as e:
            print(f"An error occurred during API call: {e}")
            break
    return all_articles

def scrape_full_content(api_article):
    """Downloads and parses the full text of an article."""
    url = api_article.get("url")
    if not url:
        return None

    try:
        article = Article(url)
        article.download()
        article.parse()
        
        return {
            "source_name": api_article.get("source", {}).get("name"),
            "title": article.title,
            "url": url,
            "published_at": api_article.get("publishedAt"),
            "full_content": article.text,
            "source_type": "article"
        }
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None

def main():
    """Main function to fetch, scrape, and save articles."""
    api_articles = fetch_all_articles()
    
    if not api_articles:
        print("No articles found. Exiting.")
        return

    scraped_data = []
    print(f"\nScraping full content for {len(api_articles)} articles using multiple threads...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_article = {executor.submit(scrape_full_content, article): article for article in api_articles}
        for future in concurrent.futures.as_completed(future_to_article):
            result = future.result()
            if result:
                scraped_data.append(result)
                print(f"Successfully scraped: {result['title'][:50]}...")

    # Save to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully saved {len(scraped_data)} articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
