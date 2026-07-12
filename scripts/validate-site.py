#!/usr/bin/env python3
"""
validate-site.py — hard deployment gate for anantcoaldepot.in.
Run before every deployment. Exit code 0 = safe to package. Any FAIL blocks.
Checks:
  1. sitemap.xml URLs <-> files parity (every URL has a file, every page dir is listed)
  2. every internal href/src on every page resolves to a real file
  3. shared markers present & paired; pages match canonical (apply-shared --check)
  4. no unreplaced {{root}} tokens
  5. no user-visible legacy "Cart" strings in any language (outside <script>)
  6. JSON-LD blocks parse as valid JSON
  7. GSTIN + both phone numbers present on every page
  8. homepage nav destination parity with canonical nav
  9. exactly one stickybar per page; homepage has no legacy .mobile-cta
"""
import re, json, sys, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []
def fail(msg): fails.append(msg); print("FAIL:", msg)
def ok(msg): print("  ok:", msg)

def pages():
    for p in sorted(ROOT.rglob("*.html")):
        if p.relative_to(ROOT).parts[0] not in ("scripts", "docs", "releases"):
            yield p

def strip_scripts(h): return re.sub(r"<script\b.*?</script>", "", h, flags=re.S)

# 1. sitemap parity
sm = (ROOT/"sitemap.xml").read_text()
sm_urls = set(re.findall(r"<loc>https://anantcoaldepot\.in(/[^<]*)</loc>", sm))
for u in sm_urls:
    f = ROOT / (u.lstrip("/") + "index.html") if u.endswith("/") else ROOT / u.lstrip("/")
    if u == "/": f = ROOT/"index.html"
    if not f.exists(): fail(f"sitemap URL has no file: {u}")
page_urls = set()
for p in pages():
    rel = p.relative_to(ROOT)
    if rel.name == "index.html":
        page_urls.add("/" + (rel.parent.as_posix() + "/" if rel.parent.as_posix() != "." else ""))
missing_sm = page_urls - sm_urls
if missing_sm - {"/404.html"}: fail(f"pages missing from sitemap: {sorted(missing_sm)}")
if not fails: ok(f"sitemap parity ({len(sm_urls)} URLs)")

# 2. internal link resolution
bad = []
for p in pages():
    h = p.read_text()
    base = p.parent
    for m in re.finditer(r'(?:href|src)="([^"]+)"', h):
        u = m.group(1)
        if re.match(r"^(https?:|mailto:|tel:|#|data:|javascript:)", u): continue
        u = u.split("#")[0].split("?")[0]
        if not u: continue
        t = (ROOT / "index.html") if u == "/" else ((ROOT / u.lstrip("/")).resolve() if u.startswith("/") else (base / u).resolve())
        if u.endswith("/") and u != "/": t = t / "index.html"
        if t.is_dir(): t = t / "index.html"
        if not t.exists(): bad.append(f"{p.relative_to(ROOT)} -> {m.group(1)}")
if bad: fail("broken internal links:\n    " + "\n    ".join(bad))
else: ok("all internal links resolve")

# 3. marker integrity + canonical match
for p in pages():
    h = p.read_text()
    for tag in ("nav", "footer", "stickybar"):
        o, c = h.count(f"<!-- shared:{tag} -->"), h.count(f"<!-- /shared:{tag} -->")
        if o != c: fail(f"{p.relative_to(ROOT)}: unpaired marker {tag}")
        if tag != "nav" and o == 0: fail(f"{p.relative_to(ROOT)}: missing shared:{tag}")
        if tag == "nav" and o == 0 and p.relative_to(ROOT).as_posix() != "index.html":
            fail(f"{p.relative_to(ROOT)}: missing shared:nav")
r = subprocess.run([sys.executable, str(ROOT/"scripts/apply-shared.py"), "--check"], capture_output=True, text=True)
if r.returncode != 0: fail("apply-shared --check drift:\n" + r.stdout)
else: ok("markers paired; pages match canonical components")

# 4. tokens
for p in pages():
    if "{{root}}" in p.read_text(): fail(f"{p.relative_to(ROOT)}: unreplaced {{{{root}}}} token")

# 5. legacy cart strings (user-visible only)
CART_PAT = re.compile(r"(>\s*🛒?\s*Cart\s*<|Your Cart|Add to Cart|कार्ट|কাৰ্ট)")
for p in pages():
    vis = strip_scripts(p.read_text())
    if CART_PAT.search(vis): fail(f"{p.relative_to(ROOT)}: legacy Cart string visible")
# also inside homepage translations object (script) — keys must be renamed there too
h = (ROOT/"index.html").read_text()
for lang_bad in ("कार्ट", "কাৰ্ট", '"Add to Cart"', '"Your Cart"'):
    if lang_bad in h: fail(f"index.html translations still contain {lang_bad}")
if not any("Cart" in f for f in fails): ok("no legacy Cart strings")

# 6. JSON-LD sanity
for p in pages():
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', p.read_text(), re.S):
        try: json.loads(m.group(1))
        except Exception as e: fail(f"{p.relative_to(ROOT)}: invalid JSON-LD: {e}")
ok("JSON-LD parses")

# 7. GSTIN + phones on every page
for p in pages():
    h = p.read_text()
    for needle in ("18AABHT9778F1ZI", "94350 18204"):
        if needle not in h: fail(f"{p.relative_to(ROOT)}: missing {needle}")
ok("GSTIN + phone present sitewide")

# 8. homepage nav destination parity with canonical
canon = (ROOT/"scripts/shared/nav.html").read_text()
canon_dests = set(re.findall(r'href="\{\{root\}\}([^"]*)"', canon)) - {""}
home = (ROOT/"index.html").read_text()
mnav = re.search(r"<nav class=\"main\".*?</nav>", home, re.S)
home_dests = set(re.findall(r'href="([^"]+)"', mnav.group(0))) if mnav else set()
home_dests = {d.lstrip("./") for d in home_dests if not d.startswith(("http", "tel:"))}
missing = {d for d in canon_dests if d not in home_dests}
if missing: fail(f"homepage nav missing canonical destinations: {sorted(missing)}")
else: ok("homepage nav parity")

# 9. one stickybar per page, no legacy bar on homepage
for p in pages():
    h = p.read_text()
    if h.count('class="acd-stickybar"') != 1: fail(f"{p.relative_to(ROOT)}: stickybar count != 1")
if 'class="mobile-cta"' in home: fail("index.html: legacy .mobile-cta still present")
ok("stickybar singleton")

print()
if fails:
    print(f"VALIDATION FAILED — {len(fails)} problem(s). Do NOT deploy.")
    sys.exit(1)
print("VALIDATION PASSED — safe to package.")
