#!/usr/bin/env python3
"""Assemble crisp 1080p MP4 videos with exact ElevenLabs audio synchronization and embedded subtitles."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PITCH_DIR = ROOT / "pitch"
DEMO_DIR = ROOT / "demo"
ASSETS = ROOT / "assets"

def build_pitch_video():
    out_mp4 = PITCH_DIR / "trialswarm_pitch_60s.mp4"
    audio_path = PITCH_DIR / "assets/audio/pitch_master_vo.mp3"
    srt_path = PITCH_DIR / "captions.srt"
    
    concat_txt = PITCH_DIR / "ffmpeg_video_concat.txt"
    concat_txt.write_text(f"""file '{ASSETS}/slide_01_hook.png'
duration 10.26
file '{ASSETS}/slide_02_trap.png'
duration 10.82
file '{PITCH_DIR}/assets/shot_workflow.png'
duration 16.49
file '{PITCH_DIR}/assets/shot_workstation.png'
duration 12.35
file '{ASSETS}/slide_05_scorecard.png'
duration 8.41
file '{ASSETS}/slide_05_scorecard.png'
""", encoding="utf-8")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio_path),
        "-i", str(srt_path),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0D1117,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-c:s", "mov_text",
        "-shortest",
        str(out_mp4)
    ]
    
    print("Building pitch video...")
    subprocess.run(cmd, check=True)
    if concat_txt.exists():
        concat_txt.unlink()
    print(f"Generated Pitch MP4: {out_mp4}")

def build_demo_video():
    out_mp4 = DEMO_DIR / "trialswarm_product_demo_3min.mp4"
    audio_path = DEMO_DIR / "assets/audio/demo_master_vo.mp3"
    srt_path = DEMO_DIR / "captions.srt"
    
    concat_txt = DEMO_DIR / "ffmpeg_demo_concat.txt"
    concat_txt.write_text(f"""file '{ASSETS}/slide_01_hook.png'
duration 27.63
file '{PITCH_DIR}/assets/shot_workflow.png'
duration 27.21
file '{PITCH_DIR}/assets/shot_workstation.png'
duration 26.84
file '{ASSETS}/slide_02_trap.png'
duration 26.47
file '{PITCH_DIR}/assets/shot_judge.png'
duration 22.06
file '{PITCH_DIR}/assets/shot_workstation.png'
duration 24.06
file '{ASSETS}/slide_05_scorecard.png'
duration 23.36
file '{ASSETS}/slide_05_scorecard.png'
""", encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio_path),
        "-i", str(srt_path),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0D1117,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-c:s", "mov_text",
        "-shortest",
        str(out_mp4)
    ]

    print("Building demo video...")
    subprocess.run(cmd, check=True)
    if concat_txt.exists():
        concat_txt.unlink()
    print(f"Generated Demo MP4: {out_mp4}")

if __name__ == "__main__":
    build_pitch_video()
    build_demo_video()
