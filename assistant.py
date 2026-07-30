import os
import json
import requests
import tools

API_KEY = ""
try:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv('GEMINI_API_KEY', '')
except:
    pass

GEMINI_AVAILABLE = bool(API_KEY and len(API_KEY) > 10)

def get_tools_context(question):
    context = ""
    q = question.lower()
    if any(w in q for w in ['search', 'find', 'what is', 'who is', 'latest', 'news', 'google']):
        context += f"Web: {tools.search_web(question)}\n"
    if any(w in q for w in ['time', 'date', 'today', 'clock', 'day']):
        context += f"Time: {tools.get_time()}\n"
    if any(w in q for w in ['video', 'youtube', 'knowledge', 'remember']):
        kc = tools.get_knowledge_context(question)
        if kc != "No knowledge base entries.":
            context += f"Knowledge: {kc}\n"
    return context

def ask_gemini(question, context):
    system = "You are ULTRON, an AI assistant. Be concise. Answer in 1-2 sentences."
    prompt = f"{system}\n"
    if context:
        prompt += f"\nContext: {context}\n"
    prompt += f"\nUser: {question}\nUltron:"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    for attempt in range(3):
        try:
            r = requests.post(url, json=data, timeout=15)
            if r.status_code == 200:
                result = r.json()
                text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text.strip() if text else "No response."
        except:
            pass
    return "Service temporarily unavailable. Try again."

def ask_fallback(question, context):
    q = question.lower()
    if context:
        return f"Based on available info: {context[:300]}"
    if any(w in q for w in ['hello', 'hi', 'hey']):
        return "ULTRON online. How can I assist?"
    if any(w in q for w in ['who are you', 'what are you']):
        return "I am ULTRON, an AI assistant. I can search the web, extract YouTube transcripts, and answer questions."
    if any(w in q for w in ['time', 'date']):
        return f"The current time is {tools.get_time()}."
    return f"ULTRON active. I can answer questions using web search and YouTube knowledge."

def ask(question):
    context = get_tools_context(question)
    if GEMINI_AVAILABLE:
        try:
            return ask_gemini(question, context)
        except Exception as e:
            return f"Gemini error: {e}. Using fallback.\n{ask_fallback(question, context)}"
    else:
        return ask_fallback(question, context)

def reset_conversation():
    pass
