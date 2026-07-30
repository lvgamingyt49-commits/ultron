import datetime
import json
import os
import requests

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge')

def get_time():
    now = datetime.datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")

def search_web(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        results = []
        if 'AbstractText' in data and data['AbstractText']:
            results.append(data['AbstractText'])
        if 'RelatedTopics' in data:
            for topic in data['RelatedTopics'][:3]:
                if 'Text' in topic:
                    results.append(topic['Text'])
        return '\n'.join(results[:5]) if results else f"No web results found for '{query}'."
    except:
        return f"Could not search for '{query}'."

def load_knowledge():
    entries = []
    if not os.path.exists(KNOWLEDGE_DIR):
        return entries
    for fname in os.listdir(KNOWLEDGE_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(KNOWLEDGE_DIR, fname), 'r', encoding='utf-8') as f:
                entries.append(json.load(f))
    return entries

def search_knowledge(query):
    entries = load_knowledge()
    q = query.lower()
    results = []
    for e in entries:
        if q in e['text'].lower():
            results.append(e)
    return results

def get_knowledge_context(query):
    entries = search_knowledge(query)
    if not entries:
        entries = load_knowledge()[:2]
    parts = []
    for e in entries:
        parts.append(f"[Video: {e.get('title', e['video_id'])}]\n{e['text'][:2000]}")
    return '\n\n'.join(parts) if parts else "No knowledge base entries."
