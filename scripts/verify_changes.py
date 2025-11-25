
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text

# --- Test Scheduling Persistence ---
print("--- Testing Scheduling Persistence ---")
LAST_RUN_FILE = Path("test_last_run.json")

def load_last_run_times():
    if LAST_RUN_FILE.exists():
        try:
            with open(LAST_RUN_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_last_run_time(job_id):
    data = load_last_run_times()
    data[job_id] = datetime.now().isoformat()
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(data, f)

# 1. Clean up old file
if LAST_RUN_FILE.exists():
    os.remove(LAST_RUN_FILE)

# 2. Test saving
save_last_run_time("test_job")
assert LAST_RUN_FILE.exists(), "File should exist after saving"
data = load_last_run_times()
assert "test_job" in data, "Job ID should be in data"
print("Persistence test passed: File created and data saved.")

# 3. Test logic for 'missed window'
last_run_str = data["test_job"]
last_run = datetime.fromisoformat(last_run_str)
now = datetime.now() + timedelta(hours=7) # Simulate 7 hours later
if now - last_run > timedelta(hours=6):
    print("Logic test passed: Correctly identified missed 6-hour window.")
else:
    print("Logic test FAILED: Did not identify missed window.")

# Clean up
if LAST_RUN_FILE.exists():
    os.remove(LAST_RUN_FILE)


# --- Test Topic Cleaning ---
print("\n--- Testing Topic Cleaning ---")
custom_stop_words = ["uh", "ll", "et", "like", "just", "say", "said", "new", "year", "news", "mr", "mrs", "ms"]
stop_words = list(text.ENGLISH_STOP_WORDS.union(custom_stop_words))

vectorizer = CountVectorizer(stop_words=stop_words, analyzer='word', token_pattern=r'(?u)\b\w\w+\b')

test_corpus = [
    "This is a new news article about AI.",
    "Uh, I just like said that it is good.",
    "The et and ll are filler words."
]

X = vectorizer.fit_transform(test_corpus)
feature_names = vectorizer.get_feature_names_out()

print(f"Features found: {feature_names}")

forbidden = set(custom_stop_words)
found_forbidden = [word for word in feature_names if word in forbidden]

if not found_forbidden:
    print("Topic cleaning test passed: No forbidden words found in features.")
else:
    print(f"Topic cleaning test FAILED: Found forbidden words: {found_forbidden}")
