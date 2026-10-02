"""Check real internal Markdown/HTML assets and obvious committed credentials."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

from src.common import ROOT


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and key in ("src", "href"):
                self.targets.append(value)


def project_files():
    """Portable discovery; excludes ignored sources/output/environments."""
    result = [ROOT / "README.md"]
    for folder in ("docs", "reports", "dashboards", "deployment"):
        result += [
            p for p in (ROOT / folder).rglob("*") if p.suffix in (".md", ".html")
        ]
    return result


class DocumentationTests(unittest.TestCase):
    def test_internal_documentation_links_and_assets_exist(self):
        checked = 0
        broken = []
        for source in project_files():
            content = source.read_text()
            if source.suffix == ".md":
                content = re.sub(r"```.*?```", "", content, flags=re.S)
                targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content)
            else:
                parser = Links()
                parser.feed(content)
                targets = parser.targets
            for target in targets:
                target = target.strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                path = (source.parent / unquote(parsed.path)).resolve()
                checked += 1
                if not path.exists() or not path.is_relative_to(ROOT):
                    broken.append(f"{source.relative_to(ROOT)} -> {target}")
        self.assertGreater(checked, 0)
        self.assertEqual(broken, [], "\n".join(broken))

    def test_deployment_dependencies_match_demo_and_secrets_are_ignored(self):
        self.assertEqual(
            (ROOT / "requirements-demo.txt").read_text(),
            (ROOT / "deployment/requirements.txt").read_text(),
        )
        ignores = (ROOT / ".gitignore").read_text()
        for pattern in (".streamlit/secrets.toml", ".env", "*.sqlite", "outputs/"):
            self.assertIn(pattern, ignores)
        # Exact patterns are deliberately assembled to avoid flagging this test.
        expressions = [
            r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"gh" + r"p_[A-Za-z0-9]{36}",
            r"github_" + r"pat_[A-Za-z0-9_]{70,}",
            r"AK" + r"IA[0-9A-Z]{16}",
        ]
        candidates = (
            project_files()
            + list((ROOT / "src").glob("*.py"))
            + [ROOT / "streamlit_app.py"]
        )
        for source in candidates:
            content = source.read_text()
            self.assertFalse(
                any(re.search(pattern, content) for pattern in expressions),
                f"Credential-like pattern in {source.relative_to(ROOT)}",
            )
