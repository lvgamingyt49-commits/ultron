import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def extract_video_id(url):
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(url_or_id):
    video_id = extract_video_id(url_or_id) if '://' in url_or_id or 'youtu' in url_or_id else url_or_id
    if not video_id:
        raise ValueError("Invalid YouTube URL or video ID")

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    try:
        transcript = transcript_list.find_transcript(['en'])
    except:
        transcript = transcript_list.find_generated_transcript(['en'])

    return transcript.fetch(), video_id

def format_transcript(entries):
    formatter = TextFormatter()
    return formatter.format_transcript(entries)

def get_transcript_with_metadata(url_or_id):
    entries, video_id = get_transcript(url_or_id)
    text = format_transcript(entries)
    return {
        'video_id': video_id,
        'text': text,
        'entries': entries
    }
