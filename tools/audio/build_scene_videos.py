#!/usr/bin/env python3
"""
五大场景演示视频生成脚本
结合场景专属原画插画与生成的环境背景音乐，输出 720p 高清 MP4 视频
"""

import subprocess
import os

SCENES = [
    {
        "id": "scene_01_greenhouse",
        "name": "温室",
        "image": "assets/backgrounds-v3/paintings/greenhouse-01.png",
        "audio": "assets/audio/bgm_01_greenhouse.wav",
        "dur": 36.0,
        "fade_out": 34.5
    },
    {
        "id": "scene_02_workshop",
        "name": "维修间",
        "image": "assets/backgrounds-v3/paintings/workshop-08.png",
        "audio": "assets/audio/bgm_02_workshop.wav",
        "dur": 36.0,
        "fade_out": 34.5
    },
    {
        "id": "scene_03_lab",
        "name": "实验室",
        "image": "assets/backgrounds-v3/paintings/lab-14.png",
        "audio": "assets/audio/bgm_03_lab.wav",
        "dur": 36.0,
        "fade_out": 34.5
    },
    {
        "id": "scene_04_bridge",
        "name": "登舰廊桥",
        "image": "assets/backgrounds-v3/paintings/bridge-14.png",
        "audio": "assets/audio/bgm_04_bridge.wav",
        "dur": 38.0,
        "fade_out": 36.5
    },
    {
        "id": "scene_05_station",
        "name": "废弃空间站",
        "image": "assets/backgrounds-v3/paintings/station-01.png",
        "audio": "assets/audio/bgm_05_station.wav",
        "dur": 40.0,
        "fade_out": 38.5
    },
]

def main():
    os.makedirs("output", exist_ok=True)
    generated_videos = []

    print("========================================")
    print("开始生成五大场景音画演示视频 (720p H.264)")
    print("========================================")

    for sc in SCENES:
        out_mp4 = f"output/{sc['id']}.mp4"
        print(f"\n[渲染中] {sc['name']} -> {out_mp4} ...")
        
        vf = f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=1,fade=t=out:st={sc['fade_out']}:d=1.5"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", sc["image"],
            "-i", sc["audio"],
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-vf", vf,
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_mp4
        ]
        
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            print(f"-> 渲染成功: {out_mp4}")
            generated_videos.append(out_mp4)
        else:
            print(f"-> 渲染失败 (code {res.returncode}): {out_mp4}")

    print("\n所有单个场景视频生成完成！")

if __name__ == "__main__":
    main()
