# Forma backend (prototype)

This folder contains a minimal TypeScript + Express + Prisma (SQLite) backend scaffold for the Forma prototype. It implements the persistence layer and basic CRUD APIs for users, teams, comparisons, suppliers, line items, flags and stated totals.

Quick start (Windows):

1. Open a terminal in `C:/Users/pieter/Downloads/forma-backend`
2. Install deps:

```bash
npm install
```

3. Generate Prisma client and push schema to SQLite DB:

```bash
npm run prisma:generate
npm run prisma:push
```

4. Start dev server:

```bash
npm run dev
```

Endpoints are under `/api` (e.g. `POST /api/comparisons`).

RFQ endpoints:
- `POST /api/rfqs` — create an RFQ with JSON `items: [{label, quantity, unit, expectedAmountCents}]`
- `GET /api/rfqs/:id` — fetch RFQ and items
- `POST /api/rfqs/:id/send` — generate a comparison pre-populated with RFQ rows

Terms extraction endpoints:
- `POST /api/comparisons/:id/extract-terms` — extract contract terms from provided `text` or an uploaded `fileId`; rule-based extractor stub for payment terms, warranty, SLA, liability, and termination. For binary files, OCR is TODO.
- `GET /api/comparisons/:id/terms` — list extracted terms for the comparison.

TCO (Total Cost) endpoint:
- `POST /api/comparisons/:id/compute-tco` — compute TCO per supplier using configurable weights. Body: `{ weights?: {...}, saveConfig?: boolean }`. Returns per-supplier breakdown and stores a `TCOResult`.

Awarding & signed report:
- `POST /api/comparisons/:id/award` — record the chosen supplier (`supplierId`) with reason and actor.
- `GET /api/comparisons/:id/award-report` — generate a PDF audit report (signed via SHA256 hash), saves it to `reports/` and returns a download URL.

Price benchmarks (anonymous):
- `GET /api/comparisons/:id/benchmarks?minN=5` — returns aggregated, anonymized statistics (mean, median, stddev, percentiles) per cost label found in the comparison. Only returns stats for a label when there are at least `minN` datapoints to avoid re-identification.

Privacy note: The endpoint never returns raw identifiers; it only returns aggregated numeric statistics and respects the minimum datapoint threshold. For production, consider differential privacy or k-anonymity techniques and an audit log for benchmark exports.

Notes: PDF generation uses `pdf-lib`. The report includes suppliers, totals, flags, terms, and a simple audit signature hash. For production, use a secure signing key and add notarization as required.

Supplier submission endpoints remain under `/submit/:token` (public tokenized URL).

TODO: add authentication, rate-limiting, production deployment guide, and supplier portal routes.
