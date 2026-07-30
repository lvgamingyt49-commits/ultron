import os
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
import tools

MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
tokenizer = None
model = None

def load():
    global tokenizer, model
    if model is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL)
        model = AutoModelForCausalLM.from_pretrained(MODEL)
    return tokenizer, model

def ask(question):
    context = ""
    q = question.lower()
    if any(w in q for w in ['search', 'find', 'what is', 'who is', 'latest', 'news', 'google']):
        context = f"Web search results: {tools.search_web(question)}"
    if any(w in q for w in ['time', 'date', 'today', 'clock', 'day']):
        context = f"Current time: {tools.get_time()}"
    if any(w in q for w in ['video', 'youtube', 'knowledge', 'remember']):
        kc = tools.get_knowledge_context(question)
        if kc != "No knowledge base entries.":
            context = f"Knowledge base:\n{kc[:1500]}"

    try:
        tok, mod = load()
    except:
        return "Model not loaded. Run: pip install transformers torch"

    messages = [
        {"role": "system", "content": "You are ULTRON, an AI assistant. Be concise. Answer in 1-3 sentences."},
    ]
    if context:
        messages.append({"role": "user", "content": f"Here is context:\n{context}"})
        messages.append({"role": "assistant", "content": "Got it. I will use that context to answer."})
    messages.append({"role": "user", "content": question})

    prompt = tok.apply_chat_template(messages, tokenize=False)
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=2048)
    out = mod.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True, pad_token_id=tok.eos_token_id)
    answer = tok.decode(out[0], skip_special_tokens=True)
    answer = answer.split("assistant")[-1].strip() if "assistant" in answer else answer.split(prompt)[-1].strip()
    return answer if answer else "I'm not sure."

def reset_conversation():
    pass
