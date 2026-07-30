import os
import re
import tools

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv('OPENAI_API_KEY', '')
    if key and 'your-api' not in key and len(key) > 10:
        OPENAI_AVAILABLE = True
        client = OpenAI(api_key=key)
except:
    pass

LOCAL_MODEL_AVAILABLE = False
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    LOCAL_MODEL_AVAILABLE = True
except:
    pass

tokenizer = None
model = None
history = []

def load_local():
    global tokenizer, model
    if model is None and LOCAL_MODEL_AVAILABLE:
        tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
        model = AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
    return tokenizer, model

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

def ask_openai(question, context):
    history.append({"role": "user", "content": question})
    messages = [{"role": "system", "content": "You are ULTRON, an AI assistant. Be concise."}]
    for msg in history[-6:]:
        messages.append(msg)
    if context:
        messages.append({"role": "system", "content": context})
    r = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, max_tokens=300)
    answer = r.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    return answer

def ask_local(question, context):
    tok, mod = load_local()
    messages = [{"role": "system", "content": "You are ULTRON. Be concise. Answer in 1-2 sentences."}]
    if context:
        messages.append({"role": "user", "content": f"Context: {context}"})
        messages.append({"role": "assistant", "content": "Understood."})
    messages.append({"role": "user", "content": question})
    prompt = tok.apply_chat_template(messages, tokenize=False)
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=1024)
    out = mod.generate(**inputs, max_new_tokens=100, temperature=0.7, do_sample=True, pad_token_id=tok.eos_token_id)
    answer = tok.decode(out[0], skip_special_tokens=True)
    if "assistant" in answer:
        answer = answer.split("assistant")[-1].strip()
    return answer if answer else "I'm not sure."

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
    if any(w in q for w in ['search', 'find']) and context:
        return context
    return f"I understand your question about '{question[:100]}'. For smarter AI responses, add an OPENAI_API_KEY to your .env file."

def ask(question):
    context = get_tools_context(question)
    if OPENAI_AVAILABLE:
        return ask_openai(question, context)
    elif LOCAL_MODEL_AVAILABLE:
        return ask_local(question, context)
    else:
        return ask_fallback(question, context)

def reset_conversation():
    global history
    history = []
