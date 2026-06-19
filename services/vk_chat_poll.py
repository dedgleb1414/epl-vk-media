import requests
from config import VK_TOKEN, USER_TOKEN, CHAT_PEER_ID_HISTORY

VOTE_THRESHOLD = 16

_state = {"poll_id": None, "alert_sent": False}


def find_latest_poll(peer_id=CHAT_PEER_ID_HISTORY):
    try:
        r = requests.get(
            "https://api.vk.com/method/messages.getHistory",
            params={"peer_id": peer_id, "count": 50, "access_token": USER_TOKEN, "v": "5.199"},
            timeout=15,
        )
        data = r.json()
        items = data.get("response", {}).get("items", [])
        for m in items:
            for a in m.get("attachments", []):
                if a.get("type") == "poll":
                    poll = a["poll"]
                    return {"poll_id": poll["id"], "owner_id": poll["owner_id"]}
        return None
    except Exception as e:
        print("Ошибка поиска опроса: " + str(e))
        return None


def get_poll_votes(poll_id, owner_id):
    try:
        r = requests.get(
            "https://api.vk.com/method/polls.getById",
            params={"poll_id": poll_id, "owner_id": owner_id, "access_token": USER_TOKEN, "v": "5.199"},
            timeout=15,
        )
        data = r.json().get("response", {})
        answers = data.get("answers", [])

        by_text = {a.get("text"): a.get("votes", 0) for a in answers}
        if "+" in by_text or "-" in by_text:
            return {"plus": by_text.get("+", 0), "minus": by_text.get("-", 0)}

        plus = answers[0].get("votes", 0) if len(answers) >= 1 else 0
        minus = answers[1].get("votes", 0) if len(answers) >= 2 else 0
        return {"plus": plus, "minus": minus}
    except Exception as e:
        print("Ошибка получения голосов: " + str(e))
        return {"plus": 0, "minus": 0}


def send_to_chat(peer_id, text):
    import random
    try:
        r = requests.post(
            "https://api.vk.com/method/messages.send",
            data={
                "peer_id": peer_id,
                "message": text,
                "random_id": random.randint(1, 999999999),
                "access_token": VK_TOKEN,
                "v": "5.199",
            },
            timeout=15,
        )
        print("send_to_chat:", r.text)
    except Exception as e:
        print("Ошибка отправки в беседу: " + str(e))


def check_and_alert(group_peer_id):
    try:
        poll = find_latest_poll()
        if not poll:
            return

        if poll["poll_id"] != _state["poll_id"]:
            _state["poll_id"] = poll["poll_id"]
            _state["alert_sent"] = False

        votes = get_poll_votes(poll["poll_id"], poll["owner_id"])

        if votes["plus"] >= VOTE_THRESHOLD and not _state["alert_sent"]:
            send_to_chat(
                group_peer_id,
                "⚠️ Набор закрыт — набралось " + str(votes["plus"]) + " человек на игру!\n"
                "Если хочешь успеть — следи за следующим сбором.",
            )
            _state["alert_sent"] = True
    except Exception as e:
        print("Ошибка check_and_alert: " + str(e))


def format_score():
    poll = find_latest_poll()
    if not poll:
        return "Актуальный опрос не найден."

    votes = get_poll_votes(poll["poll_id"], poll["owner_id"])
    free = max(VOTE_THRESHOLD - votes["plus"], 0)
    return (
        "📋 Текущая запись на игру:\n"
        "За: " + str(votes["plus"]) + "\n"
        "Против: " + str(votes["minus"]) + "\n"
        "Свободно мест: " + str(free)
    )
