import os
import sys
import json
import shutil
import subprocess
from gtts import gTTS
from icrawler.builtin import BingImageCrawler
from PIL import Image

# --- PILLOW FIX FOR PYTHON 3.13 ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import crop
from moviepy.config import change_settings

# 🛠️ IMAGEMAGICK PATH (Update this after your installation)
YOUR_MAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

if os.path.exists(YOUR_MAGICK_PATH):
    change_settings({"IMAGEMAGICK_BINARY": YOUR_MAGICK_PATH})
else:
    print(f"⚠️ WARNING: Magick not found at {YOUR_MAGICK_PATH}")

def run_production(json_file):
    if not os.path.exists(json_file):
        print(f"❌ JSON file {json_file} not found.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    TARGET_W, TARGET_H = 1080, 1920
    video_name = data.get('video_name', 'VIRAL_SHORT_2026.mp4')
    video_path = os.path.abspath(video_name)
    assets_dir = os.path.abspath('temp_assets')

    if os.path.exists(assets_dir): shutil.rmtree(assets_dir)
    os.makedirs(assets_dir, exist_ok=True)
    
    all_scene_clips = []

    for scene in data['scenes']:
        sid, txt = scene['id'], scene['text']
        search_term = scene.get('search_key', scene.get('query', 'viral news'))
        print(f"🎬 Scene {sid} | 🔍 Search: {search_term}")
        
        # 1. Download Image
        scene_dir = os.path.join(assets_dir, f"s_{sid}")
        os.makedirs(scene_dir, exist_ok=True)
        crawler = BingImageCrawler(storage={'root_dir': scene_dir})
        crawler.crawl(keyword=search_term, max_num=1, filters=dict(size='large'))
        
        # 2. Audio Generation
        audio_path = os.path.join(assets_dir, f"audio_{sid}.mp3")
        gTTS(text=txt, lang='hi').save(audio_path) 
        audio = AudioFileClip(audio_path)

        # 3. Visuals
        img_files = [os.path.join(scene_dir, f) for f in os.listdir(scene_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if img_files:
            bg_temp = os.path.join(scene_dir, "processed.jpg")
            with Image.open(img_files[0]) as img:
                img.convert("RGB").save(bg_temp)
            
            bg_clip = ImageClip(bg_temp).set_duration(audio.duration).set_audio(audio)
            w, h = bg_clip.size
            scale = max(TARGET_W/w, TARGET_H/h)
            bg_clip = bg_clip.resize(scale)
            bg_clip = crop(bg_clip, width=TARGET_W, height=TARGET_H, x_center=bg_clip.w/2, y_center=bg_clip.h/2)

            # 4. Subtitles
            txt_clip = TextClip(
                txt, 
                fontsize=75, 
                color='yellow', 
                font='Arial-Bold', 
                stroke_color='black', 
                stroke_width=2,
                method='caption', 
                size=(TARGET_W * 0.85, None) 
            ).set_duration(audio.duration).set_position(('center', 1350))

            all_scene_clips.append(CompositeVideoClip([bg_clip, txt_clip]))

    if all_scene_clips:
        print("🔗 Merging and exporting...")
        final_video = concatenate_videoclips(all_scene_clips, method="compose")
        final_video.write_videofile(video_path, fps=30, codec="libx264", audio_codec="aac")
        print(f"✅ Ready: {video_path}")

        # --- 🚀 AUTOMATED UPLOADER HANDOFF ---
        # We use os.path.join to find the uploader script in the same folder as this script
        uploader_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload_video.py")
        
        if os.path.exists(uploader_script):
            user_input = input(f"\n🚀 Video generated! Upload to YouTube? (y/n): ").lower()
            if user_input == 'y':
                title = f"{data.get('video_name', 'Viral News')} #Shorts #News 2026"
                print(f"📡 Handing off to uploader: {uploader_script}")
                # This opens the uploader in a new process
                subprocess.run([sys.executable, uploader_script, video_path, title])
                print("tune with us for more such news")
        else:
            print(f"⚠️ Uploader script not found at: {uploader_script}")

if __name__ == "__main__":
    run_production("bollywood_scenes.json")