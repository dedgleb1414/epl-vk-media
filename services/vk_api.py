import requests
import random
from config import VK_TOKEN, GROUP_ID, USER_TOKEN

def send_admin(user_id, text):
    url = "https://api.vk.com/method/messages.send"
    data = {
        "user_id": user_id,
        "message": text,
        "random_id": random.randint(1, 999999999),
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    try:
        r = requests.post(url, data=data, timeout=15)
        print(r.text)
    except requests.exceptions.RequestException as e:
        print("Ошибка отправки сообщения: " + str(e))

def get_wall_upload_server():
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    data = {
        "group_id": int(GROUP_ID),
        "access_token": USER_TOKEN,
        "v": "5.199"
    }
    r = requests.post(url, data=data)
    result = r.json()
    print("Upload server result:", result)
    return result["response"]["upload_url"]

def upload_local_photo(file_path):
    try:
        upload_url = get_wall_upload_server()
        with open(file_path, "rb") as f:
            r = requests.post(upload_url, files={"photo": ("photo.png", f, "image/png")})
        result = r.json()
        print("Upload result:", result)

        save_r = requests.post(
            "https://api.vk.com/method/photos.saveWallPhoto",
            data={
                "group_id": int(GROUP_ID),
                "photo": result["photo"],
                "server": result["server"],
                "hash": result["hash"],
                "access_token": USER_TOKEN,
                "v": "5.199"
            }
        )
        save_data = save_r.json()
        print("Save result:", save_data)

        photo = save_data["response"][0]
        return f"photo{photo['owner_id']}_{photo['id']}"

    except Exception as e:
        print(f"Ошибка загрузки локального фото: {e}")
        return None

def upload_photo_to_vk(image_url):
    try:
        img_data = requests.get(image_url, timeout=10).content
        upload_url = get_wall_upload_server()
        r = requests.post(upload_url, files={"photo": ("photo.jpg", img_data, "image/jpeg")})
        result = r.json()
        print("Upload result:", result)

        save_r = requests.post(
            "https://api.vk.com/method/photos.saveWallPhoto",
            data={
                "group_id": int(GROUP_ID),
                "photo": result["photo"],
                "server": result["server"],
                "hash": result["hash"],
                "access_token": USER_TOKEN,
                "v": "5.199"
            }
        )
        save_data = save_r.json()
        print("Save result:", save_data)

        photo = save_data["response"][0]
        return f"photo{photo['owner_id']}_{photo['id']}"

    except Exception as e:
        print(f"Ошибка загрузки фото: {e}")
        return None

def publish_post(text, attachment=None):
    url = "https://api.vk.com/method/wall.post"
    data = {
        "owner_id": f"-{GROUP_ID}",
        "message": text,
        "from_group": 1,
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    if attachment:
        data["attachments"] = attachment
    r = requests.post(url, data=data)
    print(r.text)
    return r.json()