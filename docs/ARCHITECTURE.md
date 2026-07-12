# Anant Coal Depot — Website Architecture (canonical since R1, July 2026)

## The one rule
Global components (nav, footer, mobile sticky bar) live in `scripts/shared/` ONLY.
Never edit them inside a page. Edit the canonical file, then run:

    python3 scripts/apply-shared.py     # stamps all pages
    python3 scripts/validate-site.py    # must pass
    bash scripts/package.sh r<N>        # builds releases/r<N>.zip after validating

## How it works
- Every page keeps its unique content; shared blocks sit between markers like
  `<!-- shared:footer --> ... <!-- /shared:footer -->`.
- `{{root}}` in canonical files becomes `""`, `"../"`, or `"../../"` per page depth,
  so `file://` offline preview keeps working (do NOT switch to root-absolute paths).
- The homepage keeps a bespoke header (trilingual i18n + enquiry button). The
  validator enforces that its nav covers the same destinations as the canonical nav.
- Internal tools (invoice, future Business OS modules) are separate offline HTML
  files, mobile-first (iPhone primary), designed to later fold into one PWA
  ("Anant Business"). They are not part of the website deploy.

## Deploying
Upload the CONTENTS of `releases/r<N>.zip` to Hostinger `public_html` in one
session (never partially). Rollback = upload `releases/pre-r<N>.zip` (or the
previous release zip) the same way, or `git revert` the release commit.

## Adding a page
1. Create `new-page/index.html` with real content and plain `<header>`/`<footer>`
   placeholders (or copy an existing page).
2. Run `apply-shared.py` (adopts it automatically), add it to `sitemap.xml`,
   run the validator.

## Never do
- Hand-edit anything between shared markers (next stamp overwrites it).
- Deploy without `validate-site.py` passing.
- Publish rates anywhere on the site (business rule: relationship pricing).
