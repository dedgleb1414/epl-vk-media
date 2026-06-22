import random
import requests
from config import VK_TOKEN, USER_TOKEN, CHAT_PEER_ID_HISTORY

VOTE_THRESHOLD = 16

_state = {
    "poll_id": None,
    "alert_sent": False,
    "voter_ids": [],
    "removed_ids": set(),
    "list_message_id": None,
}


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


def get_poll_data(poll_id, owner_id):
    try:
        r = requests.get(
            "https://api.vk.com/method/polls.getById",
            params={"poll_id": poll_id, "owner_id": owner_id, "access_token": USER_TOKEN, "v": "5.199"},
            timeout=15,
        )
        return r.json().get("response", {})
    except Exception as e:
        print("Ошибка получения опроса: " + str(e))
        return {}


def _plus_minus_answers(poll_data):
    answers = poll_data.get("answers", [])
    by_text = {a.get("text"): a for a in answers}
    if "+" in by_text or "-" in by_text:
        return by_text.get("+"), by_text.get("-")
    plus_a = answers[0] if len(answers) >= 1 else None
    minus_a = answers[1] if len(answers) >= 2 else None
    return plus_a, minus_a


def get_poll_votes(poll_id, owner_id):
    data = get_poll_data(poll_id, owner_id)
    plus_a, minus_a = _plus_minus_answers(data)
    plus = plus_a.get("votes", 0) if plus_a else 0
    minus = minus_a.get("votes", 0) if minus_a else 0
    return {"plus": plus, "minus": minus}


def get_voters(poll_id, owner_id, answer_id):
    try:
        r = requests.get(
            "https://api.vk.com/method/polls.getVoters",
            params={
                "owner_id": owner_id, "poll_id": poll_id, "answer_ids": answer_id,
                "access_token": USER_TOKEN, "v": "5.199",
            },
            timeout=15,
        )
        data = r.json().get("response", [])
        if data:
            return data[0].get("users", {}).get("items", [])
        return []
    except Exception as e:
        print("Ошибка получения голосовавших: " + str(e))
        return []


def get_user_names(user_ids):
    if not user_ids:
        return {}
    try:
        r = requests.get(
            "https://api.vk.com/method/users.get",
            params={"user_ids": ",".join(str(i) for i in user_ids), "access_token": USER_TOKEN, "v": "5.199"},
            timeout=15,
        )
        data = r.json().get("response", [])
        return {u["id"]: u["first_name"] + " " + u["last_name"] for u in data}
    except Exception as e:
        print("Ошибка получения имён: " + str(e))
        return {}


def send_to_chat(peer_id, text):
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
        return r.json().get("response")
    except Exception as e:
        print("Ошибка отправки в беседу: " + str(e))
        return None


def edit_chat_message(peer_id, message_id, text):
    try:
        r = requests.post(
            "https://api.vk.com/method/messages.edit",
            data={"peer_id": peer_id, "message_id": message_id, "message": text, "access_token": VK_TOKEN, "v": "5.199"},
            timeout=15,
        )
        print("edit_chat_message:", r.text)
    except Exception as e:
        print("Ошибка редактирования сообщения: " + str(e))


def delete_chat_message(peer_id, conversation_message_id):
    if not conversation_message_id:
        return
    try:
        r = requests.post(
            "https://api.vk.com/method/messages.delete",
            data={
                "peer_id": peer_id, "cmids": conversation_message_id, "delete_for_all": 1,
                "access_token": VK_TOKEN, "v": "5.199",
            },
            timeout=15,
        )
        print("delete_chat_message:", r.text)
    except Exception as e:
        print("Ошибка удаления сообщения: " + str(e))


def render_voter_list():
    active = [uid for uid in _state["voter_ids"] if uid not in _state["removed_ids"]]
    names = get_user_names(active)
    lines = ["📋 Записались на игру (16/16):"]
    for i, uid in enumerate(active):
        lines.append(str(i + 1) + ". " + names.get(uid, "ID" + str(uid)))
    lines.append("")
    lines.append("Админ вычёркивает командой: /вычеркнуть <номер>")
    return "\n".join(lines)


def update_voter_list_message(peer_id):
    text = render_voter_list()
    if _state.get("list_message_id"):
        edit_chat_message(peer_id, _state["list_message_id"], text)
    else:
        _state["list_message_id"] = send_to_chat(peer_id, text)


def remove_voter(position):
    active = [uid for uid in _state["voter_ids"] if uid not in _state["removed_ids"]]
    if position < 1 or position > len(active):
        return None
    uid = active[position - 1]
    _state["removed_ids"].add(uid)
    return uid


def check_and_alert(group_peer_id):
    try:
        poll = find_latest_poll()
        if not poll:
            return

        if poll["poll_id"] != _state["poll_id"]:
            _state["poll_id"] = poll["poll_id"]
            _state["alert_sent"] = False
            _state["voter_ids"] = []
            _state["removed_ids"] = set()
            _state["list_message_id"] = None

        data = get_poll_data(poll["poll_id"], poll["owner_id"])
        plus_a, minus_a = _plus_minus_answers(data)
        plus = plus_a.get("votes", 0) if plus_a else 0

        if plus >= VOTE_THRESHOLD and not _state["alert_sent"]:
            send_to_chat(
                group_peer_id,
                "⚠️ Набор закрыт — набралось " + str(plus) + " человек на игру!\n"
                "Если хочешь успеть — следи за следующим сбором.",
            )

            if plus_a:
                _state["voter_ids"] = get_voters(poll["poll_id"], poll["owner_id"], plus_a["id"])
            _state["removed_ids"] = set()
            _state["list_message_id"] = None
            update_voter_list_message(group_peer_id)

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
