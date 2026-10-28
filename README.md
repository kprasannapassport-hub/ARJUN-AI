# 🤖 ARJUN AI — Offline Voice Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Powered%20By-Ollama-black.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, local voice-controlled AI assistant running directly inside your terminal. Built with Python and powered by local LLMs via Ollama, ARJUN operates **100% offline without needing an active internet connection**.

---

## ✨ Key Features

* 🎙️ **Voice Command Interface:** Hands-free speech recognition and audio feedback.
* ⚡ **100% Offline & Private:** Runs entirely on your local machine via Ollama—no data leaves your system.
* 💻 **Terminal-Based Control:** Lightweight execution directly in Command Prompt or Terminal.
* 🛠️ **Multi-Language Coding:** Generates, explains, and debugs code across Python, C++, JavaScript, and more.
* 📜 **Context & History Management:** Remembers conversational flow during active sessions.

---

## 🛠️ Project Architecture

| File | Description |
| :--- | :--- |
| `arjun.py` | Core execution script and event loop |
| `voice.py` | Speech-to-text and text-to-speech audio engine |
| `llm.py` | Local Ollama model integration layer |
| `server.py` | Internal web server / API handler |
| `tools.py` | Function calling and assistant utilities |
| `config.py` | Configuration settings & wake-word parameters |
| `history.py` | Conversation context and log handling |

---

## 🚀 Quick Start Guide

### Prerequisites
1. Install [Python 3.10+](https://www.python.org/downloads/).
2. Install [Ollama](https://ollama.ai/) and pull your preferred model:
   ```bash
   ollama pull llama3.2
