# Changelog — anantcoaldepot.in

## R1 — 2026-07-12 · Shared-Components Pipeline + Website Alignment
**Version:** r1 · **Rollback:** `releases/pre-r1.zip` (or `git revert` the R1 commit)

### Summary
- NEW pipeline: `scripts/shared/` canonical nav/footer/stickybar, `apply-shared.py`
  (idempotent marker stamping, depth-aware paths), `validate-site.py` (8-point hard
  gate), `package.sh` (validate-then-zip). Docs in `docs/ARCHITECTURE.md`.
- Sitewide (all 19 pages + 404): unified 4-column footer (Products / Information /
  Contact / legal bar with GSTIN); mobile sticky Call+WhatsApp bar with iPhone
  safe-area support; subpages get full canonical nav with Industries dropdown
  (previously a stripped 3-link nav).
- Homepage: hero CTA now "Get Today's Price on WhatsApp" (primary, trilingual);
  user-type router strip (Restaurant/Dhaba · Brick Kiln · Home · Earthing ·
  Industry); "Cart" renamed to "Enquiry List" across EN/HI/AS including JS
  messages (internal storage key unchanged — no user data loss); nav restructured
  (Products · Industries ▾ · Guides · Reviews · Contact); duplicate Est-1990 stat
  removed (3-stat line); visible reviews rebalanced for diversity (Kartik Jain +
  Subham Tiwari + Hemant Agarwal; all 7 kept in DOM behind toggle); review sources
  link to Google; "See all reviews on Google" button added.
- sitemap.xml lastmod refreshed.

### Business impact
Every page now converts on mobile (sticky bar sitewide, previously homepage-only);
subpage Google landings become full entry points; industry pages discoverable from
nav+footer sitewide; enquiry mental model corrected; future global changes are a
one-file edit + one command.

### Post-deployment verification (owner checklist)
1. Google Search Console: no new coverage/usability errors within 72h.
2. Rich Results test on / and one product page: FAQ/LocalBusiness still valid.
3. Lighthouse mobile on / and /hard-coke-guwahati/: within −2 of pre-deploy score.
4. Broken-link crawl (any free crawler) over anantcoaldepot.in: zero 404s.
5. Manual mobile pass (iPhone): sticky bar on 5 pages, enquiry flow in all 3
   languages, Industries dropdown, router chips, review links.
