#!/usr/bin/env python3
import json
import sys
import random
from urllib.parse import urljoin, urlparse
from curl_cffi import requests as cffi_requests
from duckduckgo_search import DDGS
import re

DATABASE_URL = "https://raw.githubusercontent.com/hanslensy-bit/database/main/database_map.json"
LLAMA_ENDPOINT = "http://localhost:8080/v1/chat/completions"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def fetch_database():
    try:
        response = cffi_requests.get(DATABASE_URL, headers=get_headers(), timeout=5, impersonate="chrome120")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Database fetch failed: {e}", file=sys.stderr)
        return {}

def extract_text_from_url(url):
    try:
        if not url.startswith(('http://', 'https://')):
            return None
        response = cffi_requests.get(url, headers=get_headers(), timeout=5, impersonate="chrome120")
        response.raise_for_status()
        text = response.text
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:500] if len(clean) > 500 else clean
    except Exception:
        return None

def search_database(query, database):
    query_lower = query.lower()
    for key, value in database.items():
        if query_lower in key.lower():
            if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                scraped = extract_text_from_url(value)
                return scraped if scraped else value
            return value
        if isinstance(value, str) and query_lower in value.lower():
            if value.startswith('http://') or value.startswith('https://'):
                scraped = extract_text_from_url(value)
                return scraped if scraped else value
            return value
    return None

def fallback_search(query):
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            snippets = [r.get('body', '') for r in results]
            combined = ' '.join(snippets)
            return combined[:500] if len(combined) > 500 else combined
        return None
    except Exception as e:
        print(f"Search fallback failed: {e}", file=sys.stderr)
        return None

def query_llama(prompt, context=""):
    payload = {
        "model": "llama",
        "messages": [
            {"role": "system", "content": f"Context: {context}" if context else "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }
    try:
        response = cffi_requests.post(LLAMA_ENDPOINT, json=payload, timeout=30, impersonate="chrome120")
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
    except Exception as e:
        return f"Error querying llama: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 router.py '<prompt>'", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1]

    database = fetch_database()
    context = search_database(prompt, database)

    if not context:
        context = fallback_search(prompt)

    result = query_llama(prompt, context or "")
    print(result)

if __name__ == "__main__":
    main()
