"""
ARJUN SERVER - the "brain" that the Arjun phone app talks to.

Run this on the laptop (later maybe on a spare phone/PC) with:   python server.py
The phone app sends what you said; this runs the same AI brain as arjun.py and sends back:
   - the reply text
   - a list of "actions" for the phone to do (open an app, call someone, play music...)
Uses only Python's built-in web server, so nothing extra to install.
"""
import hmac
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config
import history
import tools
import arjun

PHONE_PROMPT = """You are Arjun, a friendly personal assistant for Neeraj, a first-year ECE engineering student.
He is talking to you through the Arjun app on his Android phone. Your replies are read aloud, so keep them short and natural, with no emojis or formatting.
- Reply in the same language he uses: English, Hindi (Devanagari) or Malayalam (Malayalam script).
- The phone does things for you: open_app opens an app, call_contact starts a phone call (he gets 3 seconds to cancel), play_music plays a song in Spotify, control_music does pause/next/previous/volume/mute. Use these tools whenever he asks for such things, and then say briefly what you are doing. Never just describe how he could do it himself.
- Other tools: add_task / list_tasks / complete_task / delete_task for his to-do list; search_web for current information; get_time; search_history for earlier chats; create_document makes a Word/PDF/PowerPoint file on the laptop (tell him it is saved in the Arjun files folder on the laptop).
- Never invent search results. If a tool fails, say so.
- For college work, explain and check his work so he learns; do not just hand over finished assignments.
"""

_ACTIONS = []          # actions collected while answering one request
_LOCK = threading.Lock()
_CONVOS = {}           # one short conversation memory per device


# ---- tools that only make sense on the phone: they just queue an action for the app ----
def open_app(app_name: str) -> str:
    """Open an app on the user's phone. Use the app's normal English name, such as 'WhatsApp', 'YouTube', 'Camera', 'Settings', 'Chrome'.

    Args:
        app_name: Name of the app to open.
    """
    _ACTIONS.append({"type": "open_app", "target": app_name})
    return f"The phone will open {app_name}."


def call_contact(name_or_number: str) -> str:
    """Make a phone call from the user's phone to a contact (by name, as saved in his phone) or to a number.

    Args:
        name_or_number: Contact name or phone number.
    """
    _ACTIONS.append({"type": "call", "target": name_or_number})
    return f"The phone will call {name_or_number} in 3 seconds unless the user cancels."


def play_music(song: str) -> str:
    """Play a song in the Spotify app on the user's phone right now. Use this whenever he asks to play a song, artist or music.

    Args:
        song: Song name, optionally with the artist.
    """
    _ACTIONS.append({"type": "play_music", "target": song})
    return f"The phone will play {song} on Spotify."


def control_music(action: str) -> str:
    """Control the music on the phone.

    Args:
        action: One of 'pause', 'play', 'next', 'previous', 'volume_up', 'volume_down', 'mute'.
    """
    a = action.strip().lower().replace(" ", "_")
    if a not in ("pause", "play", "next", "previous", "volume_up", "volume_down", "mute"):
        return "action must be one of: pause, play, next, previous, volume_up, volume_down, mute"
    _ACTIONS.append({"type": "media", "target": a})
    return f"The phone will do: {a}."


PHONE_TOOLS = [tools.add_task, tools.list_tasks, tools.complete_task, tools.delete_task,
               tools.search_web, tools.get_time, tools.search_history, tools.create_document,
               open_app, call_contact, play_music, control_music]


def handle_chat(text: str, device: str):
    """Run one message through the brain. Returns (reply, actions)."""
    with _LOCK:                                   # the AI model answers one question at a time
        _ACTIONS.clear()
        convo = _CONVOS.setdefault(device, [])
        history.log("user", text)
        convo.append({"role": "user", "content": text})
        del convo[:-config.MAX_HISTORY]
        system = {"role": "system", "content": PHONE_PROMPT + f"\nCurrent date/time: {tools.get_time()}"}
        try:
            reply = arjun.ask_arjun([system] + convo, PHONE_TOOLS)
        except Exception:
            convo.pop()
            raise
        convo.append({"role": "assistant", "content": reply})
        history.log("assistant", reply)
        return reply, list(_ACTIONS)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/ping":
            self._send(200, {"ok": True, "name": "Arjun"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, {"error": "not found"})
        sent = self.headers.get("X-Token", "")
        if not hmac.compare_digest(sent.encode(), config.SERVER_TOKEN.encode()):
            return self._send(401, {"error": "wrong token"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(body.get("text", "")).strip()
            device = str(body.get("device", "phone"))
            if not text:
                return self._send(400, {"error": "empty message"})
            print(f"[{device}] {text}")
            reply, actions = handle_chat(text, device)
            print(f"[Arjun] {reply}   actions={actions}")
            self._send(200, {"reply": reply, "actions": actions})
        except Exception as e:
            print("[error]", e)
            self._send(500, {"error": str(e)})

    def log_message(self, *args):       # keep the console quiet
        pass


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))     # no data is sent; just finds our Wi-Fi address
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    if len(config.SERVER_TOKEN) < 8:
        print("Set SERVER_TOKEN in config.py first (at least 8 characters - make it long and random).")
        print("Idea: run   python -c \"import secrets; print(secrets.token_urlsafe(16))\"")
        return
    server = ThreadingHTTPServer(("0.0.0.0", config.SERVER_PORT), Handler)
    print("Arjun server is running.")
    print(f"In the phone app, set the server address to:  http://{lan_ip()}:{config.SERVER_PORT}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
