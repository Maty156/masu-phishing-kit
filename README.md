# 🎣 MASU Phishing Kit

> **Educational use only.** Built for [MASU Cyber Academy](https://masu-cyber-academy.onrender.com) — a free cybersecurity learning platform for Ethiopian students.

A command-line phishing page cloner for ethical hacking training. Clone a login page, serve it locally, and capture submitted credentials — all in a controlled lab environment.

---

## ⚠️ Legal Disclaimer

This tool is for **authorized penetration testing and educational purposes only**.  
Using this tool against systems you do not own or have explicit written permission to test is **illegal** under Ethiopian law and international cybercrime statutes.

By using this tool, you confirm you are operating in a controlled lab environment or have written authorization from the target system's owner.

---

## Features

- 🌐 **Page cloner** — downloads HTML, CSS, JS, and image assets
- 💉 **Form injector** — intercepts all form submissions without breaking page UI
- 🖥️ **Local HTTP server** — serves the cloned page with capture endpoint
- 🗄️ **SQLite logger** — stores all captures with timestamp and IP
- 📋 **Log viewer** — view captured credentials from the CLI
- 🔄 **Auto-redirect** — victim is redirected to the real site after capture

---

## Installation

```bash
git clone https://github.com/Maty156/masu-phishing-kit
cd masu-phishing-kit
chmod +x run.sh
```

### Arch Linux (and any PEP 668 distro)

Arch blocks system-wide `pip install`. Use the included `run.sh` which auto-creates a venv on first run:

```bash
./run.sh              # sets up venv + installs deps automatically on first launch
./run.sh demo         # subsequent runs — no manual activate needed
```

Or manually:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python masu-phish.py
```

### Other distros / Kali / Ubuntu

```bash
pip install -r requirements.txt
python3 masu-phish.py
```

---

## Usage

### 1. Quick demo (no internet needed)
```bash
./run.sh demo                        # generic corporate login
./run.sh demo cloudmail              # M365-style email login
```

### 2. Clone a real page
```bash
./run.sh clone https://example.com/login
```

### 3. Serve a previously cloned page
```bash
./run.sh serve          # default port 8080
./run.sh serve 9090     # custom port
```

### 4. View captured credentials
```bash
./run.sh logs
./run.sh logs --export captures.json
```

### 5. List built-in templates
```bash
./run.sh templates
```

### 6. Clear everything
```bash
./run.sh clear
```

---

## How it works

```
Target URL
    │
    ▼
[Cloner] ──► Downloads HTML + assets ──► Rewrites paths to local
    │
    ▼
[Injector] ──► Patches <form> actions ──► Injects JS capture hook
    │
    ▼
output/index.html   ◄── served by PhishServer
    │
    ├── GET  /           ──► serves cloned page
    ├── POST /capture    ──► receives JSON from JS hook
    ├── POST /capture-form ► receives standard form POST
    └── GET  /redirect   ──► 302 → real site
                │
                ▼
           [Logger] ──► credentials.db (SQLite)
                    ──► credentials.log (plaintext)
```

---

## Project structure

```
masu-phishing-kit/
├── masu-phish.py          # CLI entry point
├── requirements.txt
├── cloner/
│   └── cloner.py          # Page fetcher + asset downloader + injector
├── server/
│   └── server.py          # HTTP server + capture handler
├── logger/
│   └── logger.py          # SQLite + plaintext logger
└── output/                # Generated files (gitignored)
    ├── index.html
    ├── assets/
    ├── credentials.db
    ├── credentials.log
    └── meta.txt
```

---

## Lab setup (recommended)

Run this inside a VM or isolated network. To test locally:

1. Clone `https://example.com` or any demo login page
2. `python3 masu-phish.py serve`
3. Open `http://localhost:8080` in a browser
4. Submit the form
5. `python3 masu-phish.py logs` to see the capture

---

## Part of the MASU toolkit

| Tool | Description |
|------|-------------|
| [masu-recon](https://github.com/Maty156/masu-recon) | Recon framework (WHOIS, DNS, Nmap, subdomains) |
| [masu-phishing-kit](https://github.com/Maty156/masu-phishing-kit) | Educational phishing page cloner |
| [masu-terminal-installer](https://github.com/Maty156/masu-terminal-installer) | ZSH + Powerlevel10k auto-installer |
| [masu-hyprland-installer](https://github.com/Maty156/masu-hyprland-installer) | Hyprland rice installer |

---

*Built from Addis Ababa. Running on Arch + Hyprland.*
