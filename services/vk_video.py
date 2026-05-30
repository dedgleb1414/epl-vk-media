import requests
import os
import subprocess
from config import VK_TOKEN, GROUP_ID, USER_TOKEN

YT_DLP = "D:\\epl-vk-media\\yt-dlp.exe"

def download_video(youtube_url, output_path="data/clip.mp4"):
    try:
        if os.path.exists(output_path):
            os.remove(output_path)

        # Сначала пробуем 720p+ с ffmpeg
        cmd = [
            YT_DLP,
            "-f", "bestvideo[height>=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=720]+bestaudio/best[height>=720]/best",
            "-o", output_path,
            "--no-playlist",
            "--merge-output-format", "mp4",
            youtube_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / 1024 / 1024
            print("Видео скачано: " + output_path + " (" + str(round(size_mb, 1)) + " MB)")
            return output_path

        # Запасной вариант — лучшее mp4 без слияния
        print("Пробую запасной формат...")
        cmd2 = [
            YT_DLP,
            "-f", "best[ext=mp4]/best",
            "-o", output_path,
            "--no-playlist",
            youtube_url
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)

        if result2.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / 1024 / 1024
            print("Видео скачано (запасной): " + output_path + " (" + str(round(size_mb, 1)) + " MB)")
            return output_path

        print("Ошибка скачивания: " + result2.stderr[:300])
        return None

    except Exception as e:
        print("Ошибка yt-dlp: " + str(e))
        return None

def get_video_upload_server(title):
    url = "https://api.vk.com/method/video.save"
    data = {
        "name": title,
        "group_id": int(GROUP_ID),
        "wallpost": 0,
        "access_token": USER_TOKEN,
        "v": "5.199"
    }
    r = requests.post(url, data=data)
    result = r.json()
    print("Video save result:", result)
    return result.get("response", {})

def upload_video_to_vk(file_path, title):
    try:
        response = get_video_upload_server(title)
        upload_url = response.get("upload_url")
        video_id = response.get("video_id")
        owner_id = response.get("owner_id")

        if not upload_url:
            print("Нет upload_url")
            return None

        with open(file_path, "rb") as f:
            r = requests.post(upload_url, files={"video_file": f}, timeout=300)
        print("Upload response:", r.text)

        if os.path.exists(file_path):
            os.remove(file_path)

        if video_id and owner_id:
            return "video" + str(owner_id) + "_" + str(video_id)
        return None

    except Exception as e:
        print("Ошибка загрузки видео: " + str(e))
        return None