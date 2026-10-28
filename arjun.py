"""
ARJUN - your personal local AI assistant.

The big idea:
  1. You type a message, or press Enter and speak.
  2. We send it to a small AI model running ON YOUR LAPTOP (through Ollama).
  3. The model answers directly, or asks us to run one of our Python functions
     ("tools" in tools.py) such as add_task, search_web, create_document.
  4. We run the function, hand the result back, and Arjun replies - in text and voice.
"""
import sys

try:
    import ollama
except ImportError:           # e.g. on the Termux phone: use our built-in mini client
    import llm as ollama

import config
import history
import tools

SYSTEM_PROMPT = """You are Arjun, a friendly personal assistant for Neeraj, a first-year ECE engineering student.
- Reply in the same language the user writes in: English, Hindi (Devanagari script) or Malayalam (Malayalam script). If he mixes languages, you can mix too.
- Keep replies short and clear unless he asks for detail. Your replies may be read aloud, so avoid emojis and heavy formatting.
- Use tools when needed: add_task / list_tasks / complete_task / delete_task for the to-do list; search_web for anything current or that you are unsure about; get_time for date and time; search_history to find things said in earlier conversations; add_contact / call_contact for phone calls; create_document to make Word, PDF or PowerPoint files; play_music to play a song in the Spotify app (it starts the song itself - never reply with just a link); control_music for pause, resume, next, previous, volume and mute.
- For create_document: first write the complete, useful content yourself, then call the tool once. Tell him the file location afterwards.
- Never invent search results or file locations. If a tool fails, say so.
- When helping with college work, explain concepts and check his work so he learns; do not just hand over finished assignments.
"""

HELP = """Commands:
  (just press Enter)   speak to Arjun
  /voice               turn spoken replies on/off
  /history             show the last 10 messages
  /history words       search old conversations, e.g. /history capacitor
  /help                show this
  exit                 quit
"""


def ask_arjun(messages, tool_list=None):
    """Send the conversation to the model, run any tools it asks for, return the final reply."""
    tool_list = tool_list or tools.TOOLS
    lookup = {fn.__name__: fn for fn in tool_list}
    for _ in range(6):                       # safety limit so it can never loop forever
        response = ollama.chat(model=config.MODEL, messages=messages, tools=tool_list)
        msg = response.message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            name, args = call.function.name, call.function.arguments
            print(f"   (Arjun is using: {name})")
            try:
                result = lookup[name](**args)
            except Exception as e:
                result = f"Error running {name}: {e}"
            messages.append({"role": "tool", "tool_name": name, "content": str(result)})
    return "Sorry, I got stuck. Please try again."


def main():
    # Lets the Windows terminal show Hindi / Malayalam letters
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    try:
        import voice
        voice_ready = True
    except Exception:
        voice = None
        voice_ready = False
    speak_on = config.SPEAK_REPLIES and voice_ready

    print("Arjun is ready.  Type a message, or press Enter to speak.  /help for commands.\n")
    system = {"role": "system", "content": SYSTEM_PROMPT + f"\nCurrent date/time: {tools.get_time()}"}
    convo = []

    while True:
        text = input("You: ").strip()

        if text == "":                                   # push-to-talk
            if not voice_ready:
                print("Voice isn't set up yet - see the README.\n")
                continue
            print("   Listening... speak now.")
            try:
                text = voice.listen()
            except Exception as e:
                print(f"   [microphone/Whisper problem: {e}]\n")
                continue
            if not text:
                print("   (I didn't hear anything)\n")
                continue
            print(f"You said: {text}")

        low = text.lower()
        if low in ("exit", "quit", "bye", "/exit"):
            print("Arjun: Bye!")
            break
        if low == "/help":
            print(HELP)
            continue
        if low == "/voice":
            if not voice_ready:
                print("Voice isn't set up yet - see the README.\n")
            else:
                speak_on = not speak_on
                print(f"Spoken replies: {'ON' if speak_on else 'OFF'}\n")
            continue
        if low.startswith("/history"):
            query = text[len("/history"):].strip()
            rows = history.search(query, 10) if query else history.recent(10)
            print(history.format_rows(rows) + "\n")
            continue

        history.log("user", text)
        convo.append({"role": "user", "content": text})
        convo = convo[-config.MAX_HISTORY:]
        try:
            reply = ask_arjun([system] + convo)
        except Exception as e:
            print(f"\n[Problem talking to the model: {e}]")
            print(f"Is Ollama running? Did you run: ollama pull {config.MODEL}\n")
            convo.pop()
            continue
        convo.append({"role": "assistant", "content": reply})
        history.log("assistant", reply)
        print(f"\nArjun: {reply}\n")
        if speak_on:
            voice.speak(reply)


if __name__ == "__main__":
    main()
