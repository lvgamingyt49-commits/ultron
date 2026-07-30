import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from transcript import get_transcript_with_metadata
from assistant import ask, reset_conversation
from tools import load_knowledge, search_knowledge, get_knowledge_context
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge')
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

app = Flask(__name__)

@app.route('/')
def index():
    videos = load_knowledge()
    return render_template('index.html', videos=videos)

@app.route('/api/add', methods=['POST'])
def add_video():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')

    try:
        result = get_transcript_with_metadata(url)
        entry = {
            'video_id': result['video_id'],
            'title': title or result['video_id'],
            'text': result['text'],
            'added_at': __import__('datetime').datetime.now().isoformat()
        }
        path = os.path.join(KNOWLEDGE_DIR, f'{result["video_id"]}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
        return jsonify({'success': True, 'video_id': result['video_id'], 'title': entry['title']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/videos')
def list_videos():
    return jsonify(load_knowledge())

@app.route('/api/search')
def search_videos():
    q = request.args.get('q', '')
    return jsonify(search_knowledge(q))

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'answer': 'Ask me something.'})
    answer = ask(question)
    return jsonify({'answer': answer})

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    reset_conversation()
    return jsonify({'success': True})

@app.route('/api/remove/<video_id>', methods=['DELETE'])
def remove_video(video_id):
    path = os.path.join(KNOWLEDGE_DIR, f'{video_id}.json')
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    if not client:
        return jsonify({'error': 'No API key'}), 400
    try:
        response = client.audio.speech.create(model='tts-1', voice='nova', input=text)
        audio_path = os.path.join(os.path.dirname(__file__), 'static', 'ultron_speech.mp3')
        response.stream_to_file(audio_path)
        return jsonify({'audio_url': '/static/ultron_speech.mp3'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
