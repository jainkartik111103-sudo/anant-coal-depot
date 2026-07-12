#!/usr/bin/env python3
"""
apply-shared.py — Anant Coal Depot shared-components pipeline.

Stamps canonical components (scripts/shared/*.html) into every page between
markers, rewriting {{root}} to the correct relative depth per page.

  <!-- shared:nav -->       header/nav        (subpages + 404 only; homepage
                                               keeps its bespoke i18n header —
                                               validator enforces destination
                                               parity instead)
  <!-- shared:footer -->    footer            (ALL pages)
  <!-- shared:stickybar --> mobile action bar (ALL pages)

Idempotent: re-running replaces marker contents only. First run performs
adoption: replaces a page's existing <header>/<footer>/.mobile-cta with
marker blocks.

Usage:  python3 scripts/apply-shared.py [--check]
        --check  verify pages match canonical output; exit 1 on drift (no writes)
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARED = ROOT / "scripts" / "shared"
CHECK = "--check" in sys.argv

def pages():
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in ("scripts", "docs", "releases"):
            continue
        out.append(p)
    return out

def depth_prefix(p: pathlib.Path) -> str:
    return "../" * (len(p.relative_to(ROOT).parts) - 1)

def load(name: str) -> str:
    return (SHARED / name).read_text(encoding="utf-8").strip()

def block(tag: str, body: str) -> str:
    return f"<!-- shared:{tag} -->\n{body}\n<!-- /shared:{tag} -->"

def stamp(html: str, tag: str, body: str) -> str:
    pat = re.compile(r"<!-- shared:%s -->.*?<!-- /shared:%s -->" % (tag, tag), re.S)
    if pat.search(html):
        return pat.sub(lambda m: block(tag, body), html, count=1)
    return html  # marker absent; adoption handles insertion

def adopt(html: str, page: pathlib.Path, tag: str, body: str) -> str:
    """First-time insertion of a marker block into a page without one."""
    b = block(tag, body)
    if f"<!-- shared:{tag} -->" in html:
        return html
    if tag == "nav":
        m = re.search(r"<header\b.*?</header>", html, re.S)
        if m:
            return html[:m.start()] + b + html[m.end():]
        return re.sub(r"(<body[^>]*>)", r"\1\n" + b.replace("\\", "\\\\"), html, count=1)
    if tag == "footer":
        m = re.search(r"<footer\b.*?</footer>", html, re.S)
        if m:
            return html[:m.start()] + b + html[m.end():]
        return html.replace("</body>", b + "\n</body>", 1)
    if tag == "stickybar":
        # replace a legacy .mobile-cta bar if present, else insert before </body>
        m = re.search(r'<!-- MOBILE STICKY CTA -->\s*<div class="mobile-cta">.*?</div>', html, re.S)
        if m:
            return html[:m.start()] + b + html[m.end():]
        return html.replace("</body>", b + "\n</body>", 1)
    raise ValueError(tag)

def main():
    nav, foot, bar = load("nav.html"), load("footer.html"), load("stickybar.html")
    drift = []
    for page in pages():
        html = page.read_text(encoding="utf-8")
        root = depth_prefix(page)
        is_home = page.relative_to(ROOT).as_posix() == "index.html"
        new = html
        for tag, canon in (("nav", nav), ("footer", foot), ("stickybar", bar)):
            if tag == "nav" and is_home:
                continue  # bespoke i18n header; parity enforced by validator
            body = canon.replace("{{root}}", root)
            # root form of "{{root}}#products" from the homepage would be "#products",
            # from subpages "../#products" — both correct.
            new = adopt(stamp(new, tag, body), page, tag, body)
        if new != html:
            if CHECK:
                drift.append(str(page.relative_to(ROOT)))
            else:
                page.write_text(new, encoding="utf-8")
                print("stamped:", page.relative_to(ROOT))
    if CHECK:
        if drift:
            print("DRIFT — pages out of sync with canonical components:")
            for d in drift: print("  ", d)
            sys.exit(1)
        print("check OK: all pages match canonical components")
    else:
        print("done.")

if __name__ == "__main__":
    main()
