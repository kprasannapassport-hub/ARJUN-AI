"""
A tiny Ollama client that uses ONLY Python's built-in libraries.

arjun.py uses it automatically when the 'ollama' package isn't installed
(for example on the Termux phone, where that package is hard to install).
It answers in the same shape as ollama.chat(), so the rest of the code doesn't care.
"""
import inspect
import json
import os
import re
import typing
import urllib.error
import urllib.request

import config

_JSON_TYPES = {int: "integer", float: "number", bool: "boolean", str: "string"}


class _Function:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, function):
        self.function = function


class Message:
    def __init__(self, content="", tool_calls=None, role="assistant"):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls

    def to_dict(self):
        d = {"role": self.role, "content": self.content or ""}
        if self.tool_calls:
            d["tool_calls"] = [
                {"function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in self.tool_calls
            ]
        return d


class Response:
    def __init__(self, message):
        self.message = message


def _host():
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    if not host.startswith("http"):
        host = "http://" + host
    return host.rstrip("/")


def _schema(fn):
    """Turn a Python function (with type hints and a docstring) into the tool description Ollama wants."""
    doc = inspect.getdoc(fn) or ""
    description = re.split(r"\n\s*Args:", doc)[0].strip()
    arg_docs = {}
    if "Args:" in doc:
        for line in doc.split("Args:", 1)[1].splitlines():
            m = re.match(r"^\s+(\w+):\s*(.*)$", line)
            if m:
                arg_docs[m.group(1)] = m.group(2).strip()
    hints = typing.get_type_hints(fn)
    props, required = {}, []
    for name, param in inspect.signature(fn).parameters.items():
        props[name] = {"type": _JSON_TYPES.get(hints.get(name, str), "string"),
                       "description": arg_docs.get(name, "")}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    return {"type": "function",
            "function": {"name": fn.__name__, "description": description,
                         "parameters": {"type": "object", "properties": props, "required": required}}}


def chat(model, messages, tools=None, **kwargs):
    payload = {
        "model": model,
        "stream": False,
        "messages": [m if isinstance(m, dict) else m.to_dict() for m in messages],
        "options": {"num_ctx": config.NUM_CTX},
        "keep_alive": "30m",                 # keep the model in memory between questions
    }
    if tools:
        payload["tools"] = [_schema(f) for f in tools]
    req = urllib.request.Request(
        _host() + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Ollama error {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Can't reach Ollama ({e.reason}). Is 'ollama serve' running?")

    msg = data.get("message", {})
    calls = []
    for c in msg.get("tool_calls") or []:
        args = c["function"].get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                args = {}
        calls.append(_ToolCall(_Function(c["function"]["name"], args)))
    return Response(Message(msg.get("content", ""), calls or None))
