from gtts import gTTS
from moviepy import TextClip, AudioFileClip, CompositeVideoClip
import os
import uuid


def speak_text(text: str, output_dir="temp") -> str:
    """Generate audio from text using gTTS."""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"tts_{uuid.uuid4().hex}.mp3")
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    return filename


def create_video_with_audio(text: str, audio_path: str, output_dir="temp") -> str:
    """Generate a simple video with subtitles and audio."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"video_{uuid.uuid4().hex}.mp4")
    
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    txt_clip = TextClip(text, fontsize=30, color='white', bg_color='black', size=(720, 128))
    txt_clip = txt_clip.set_duration(duration).set_position('bottom')

    video = CompositeVideoClip([txt_clip]).set_audio(audio_clip)
    video.write_videofile(output_path, fps=24, codec='libx264')

    return output_path
