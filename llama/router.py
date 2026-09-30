#!/usr/bin/env python3
import json
import sys
import requests
from urllib.parse import urlencode

DATABASE_URL = "https://raw.githubusercontent.com/hanslensy-bit/database/main/database_map.json"
DUCKDUCKGO_API = "https://api.duckduckgo.com/"
LLAMA_ENDPOINT = "http://localhost:8080/v1/chat/completions"

def fetch_database():
    try:
        response = requests.get(DATABASE_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Database fetch failed: {e}", file=sys.stderr)
        return {}

def search_database(query, database):
    for key, value in database.items():
        if query.lower() in key.lower() or (isinstance(value, str) and query.lower() in value.lower()):
            return value
    return None

def fallback_search(query):
    try:
        params = {"q": query, "format": "json"}
        response = requests.get(DUCKDUCKGO_API, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("AbstractText"):
            return data["AbstractText"]
        if data.get("Results"):
            return " ".join([r.get("Text", "") for r in data["Results"][:3]])
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
        response = requests.post(LLAMA_ENDPOINT, json=payload, timeout=30)
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