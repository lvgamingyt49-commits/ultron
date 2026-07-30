let isRecording = false;
let recognition = null;
let selectedVideoId = null;

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.onresult = function(e) {
        const text = e.results[0][0].transcript;
        document.getElementById('questionInput').value = text;
        stopRecording();
        askUltron();
    };
    recognition.onerror = function() { stopRecording(); };
    recognition.onend = function() { stopRecording(); };
}

function toggleVoice() {
    if (!recognition) { addMessage('system', 'Voice not supported in this browser.'); return; }
    if (isRecording) { stopRecording(); }
    else { startRecording(); }
}

function startRecording() {
    isRecording = true;
    document.getElementById('voiceBtn').classList.add('recording');
    try { recognition.start(); } catch(e) { stopRecording(); }
}

function stopRecording() {
    isRecording = false;
    document.getElementById('voiceBtn').classList.remove('recording');
    try { recognition.stop(); } catch(e) {}
}

function addVideo() {
    const url = document.getElementById('videoUrl').value.trim();
    const title = document.getElementById('videoTitle').value.trim();
    const status = document.getElementById('addStatus');
    if (!url) { status.className = 'status error'; status.textContent = 'ERROR: No URL provided'; return; }

    status.className = 'status'; status.textContent = 'INGESTING...';
    fetch('/api/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title })
    })
    .then(r => r.json())
    .then(d => {
        if (d.success) {
            status.className = 'status success';
            status.textContent = `SUCCESS: ${d.title}`;
            document.getElementById('videoUrl').value = '';
            document.getElementById('videoTitle').value = '';
            refreshVideoList();
        } else {
            status.className = 'status error';
            status.textContent = 'ERROR: ' + d.error;
        }
    })
    .catch(e => { status.className = 'status error'; status.textContent = 'ERROR: ' + e.message; });
}

function refreshVideoList() {
    fetch('/api/videos').then(r => r.json()).then(videos => {
        const list = document.getElementById('videoList');
        list.innerHTML = videos.map(v =>
            `<div class="video-card" data-id="${v.video_id}" onclick="selectVideo('${v.video_id}')">
                <div class="card-title">${v.title}</div>
                <div class="card-meta">${v.added_at.slice(0, 10)}</div>
                <button class="btn-remove" onclick="event.stopPropagation(); removeVideo('${v.video_id}')">DELETE</button>
            </div>`
        ).join('');
    });
}

function searchVideos() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) { refreshVideoList(); return; }
    fetch('/api/search?q=' + encodeURIComponent(q))
        .then(r => r.json())
        .then(videos => {
            const list = document.getElementById('videoList');
            list.innerHTML = videos.map(v =>
                `<div class="video-card" data-id="${v.video_id}">
                    <div class="card-title">${v.title}</div>
                    <div class="card-meta">${v.added_at.slice(0, 10)}</div>
                    <button class="btn-remove" onclick="event.stopPropagation(); removeVideo('${v.video_id}')">DELETE</button>
                </div>`
            ).join('');
        });
}

function removeVideo(videoId) {
    fetch('/api/remove/' + videoId, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => { if (d.success) { refreshVideoList(); addMessage('system', 'Knowledge entry removed.'); } });
}

function selectVideo(videoId) {
    selectedVideoId = selectedVideoId === videoId ? null : videoId;
    document.querySelectorAll('.video-card').forEach(c => c.style.borderColor = '');
    if (selectedVideoId) {
        document.querySelector(`.video-card[data-id="${videoId}"]`).style.borderColor = '#2ec4b6';
    }
}

function askUltron() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question) return;

    addMessage('user', question);
    input.value = '';

    const typingMsg = addMessage('assistant', 'Processing...');
    document.getElementById('statusText').textContent = 'PROCESSING';

    fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    })
    .then(r => r.json())
    .then(d => {
        typingMsg.remove();
        addMessage('assistant', d.answer);
        document.getElementById('statusText').textContent = 'READY';
    })
    .catch(e => {
        typingMsg.remove();
        addMessage('system', 'ERROR: ' + e.message);
        document.getElementById('statusText').textContent = 'ERROR';
    });
}

function resetChat() {
    fetch('/api/reset', { method: 'POST' })
        .then(() => {
            document.getElementById('chatMessages').innerHTML =
                `<div class="message system"><span class="msg-icon">&gt;&gt;</span>ULTRON online. Conversation reset.</div>`;
            addMessage('system', 'Conversation history cleared.');
        });
}

function addMessage(role, text) {
    const messages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

function updateClock() {
    const now = new Date();
    document.getElementById('clockDisplay').textContent =
        now.toLocaleTimeString('en-US', { hour12: false });
}

document.getElementById('questionInput').addEventListener('keypress', e => { if (e.key === 'Enter') askUltron(); });
document.getElementById('videoUrl').addEventListener('keypress', e => { if (e.key === 'Enter') addVideo(); });

initSpeechRecognition();
setInterval(updateClock, 1000);
updateClock();
