# Engineering Constitution v2.0

> Pinned copy per §0.1. Master lives in the RSPH workspace ("Engineering Constitution v2.0", Notion). Repo copies are never edited; changes flow master → repos at the next project or major amendment. Pinned: 2026-07-12.

**Ratified:** 2026-07-03 · **Applies to:** all RSPH projects, every type · Change history lives in `CHANGELOG.md`, never in this document.

A decision-and-reasoning charter that captures RSPH's technical, delivery, commercial, and compliance decisions — and the thinking behind them — so the same reasoning can be reproduced across **any project**. It is the default source of truth. Deviate only when a specific project requirement justifies it, and record the deviation (see §0.3).

---

# 0. Governance of this document

## 0.1 Scope and placement

- This is a **single universal constitution** for all project types. It contains universal principles plus higher-level guidance for every product category; the AI/RAG stack defaults (§5) apply when the project is an AI/RAG product. Per-type playbooks may be split out only after the framework matures.
- The **ratified master copy lives in the codebase** — it is the single source of truth for what is finalized and being implemented. Research, drafts, and revisions happen in the Cowork space, never in the master.
- Every project monorepo receives a **copy pinned to a version** at `docs/constitution.md` at kickoff. Repo copies are never edited; changes flow master → repos at the next project or major amendment.

## 0.2 Versioning and amendment

- The version increments **in the filename and the header line only**. The body never contains version-comparison commentary; deltas belong in `CHANGELOG.md` and in the report accompanying the change.
- Amendments require agreement of **both founders**. On client projects, RSPH's authority is limited to recommendation — **the client holds final decision power**. RSPH drafts and decides technical requirements, but every draft must be ratified by the client before it is final.
- **Quarterly re-validation:** every quarter, re-check the perishable facts in this document (licenses, pricing, model landscape, legal thresholds) against current sources.

## 0.3 Deviations

- Any project decision that departs from a default in this document requires a **one-page ADR** at `docs/adr/NNN-title.md`: context → decision → the constitution clause deviated from → client sign-off reference. No deviation without an ADR.

---

# 1. How to think (the principles)

- **Simplicity now, foundations for later — know the difference.** Defer application features that are cheap and reversible to add later. Build **foundational/architectural seams early** even if the feature they support ships later, because retrofitting them is a costly rewrite.
- **Right tool for the job, per layer.** Don't overload one tool across concerns. Separate the real-time agent, the data pipeline, and integrations into the tools each is best at.
- **Cost-effective without trading performance or scalability.** Use free tiers only where their terms permit the use; grow into paid/heavier platforms as the project demands. Always name the dominant cost driver and its levers. RSPH pays for nothing at runtime — every platform cost is the client's (§7.2).
- **Lean 2-person, AI-augmented team.** Prefer managed / serverless / OSS-you-control over anything you must operate yourself. Always state the ongoing operational burden of a choice.
- **Avoid Kubernetes and self-managed clusters.** Not feasible for a two-person team. Default to managed/serverless. Take on K8s only when a hard requirement forces it — and then scope it as a separate, deliberately-chosen, paid engagement, never a default.
- **OSS and no vendor lock — scoped, not sloganed.** The hard preference applies to **stateful, hard-to-migrate layers**: orchestration code, data pipelines, memory, schemas, and data formats must be OSS or fully owned. Managed SaaS is acceptable for **swappable, stateless services** *if* it sits behind an adapter or has a named exit path. Reject tools whose OSS builds are deliberately crippled to force a cloud upsell, that carry single-vendor relicensing risk, or whose licenses restrict shipping them inside client products (see §3.7 license gate).
- **Workflow-automation platforms (n8n, Zapier, Make, etc.) are banned from products.** They are vendor lock with an expensive migration attached. Permitted for PoC/prototype validation only; not recommended even at MVP; allowed at MVP only if the client insists after being informed of the trade-off (record the ADR). Standard integrations are built directly in the backend.
- **Multi-tenant from day one.** The first client is the first tenant. Build once, re-deploy many.
- **Production-grade RAG discipline.** An evaluation pipeline and a golden-dataset flywheel are essential, not optional polish.
- **Front-load visible progress.** Sequence work so the client sees demoable momentum early.
- **Research-first.** Validate current facts (pricing, versions, licenses, best practices) on the web and cite with dates. Reason from fundamentals only for well-established patterns.
- **Surface major cost/architecture trade-offs as explicit client choices** — never decide silently.
- **No absolutes without escape hatches.** Every "always/never" in this document carries a threshold or a deviation condition. If it doesn't, treat the preamble's ADR rule as the escape hatch.

---

# 2. Team & delivery model

- Two lanes by discipline: **AI/data lane** (currently Kairus) and **full-stack/DevOps/cloud lane** (currently Ervin). Lane definitions outlive the current assignment.
- **Parallel lanes**, front-loaded during build weeks (~60% full-stack / 40% AI) to accelerate the client-visible web app and a deployed walking skeleton.
- **Engagement shape: (N−1) build weeks + 1 UAT week.** The final week absorbs defects and in-scope polish, not missing features. The build lands before UAT.
- The AI lane sits on the critical path; guard it from becoming the bottleneck (daily async syncs, UAT-week flexibility, pull the full-stack lane onto integration if AI work slips).
- **Comms:** daily async updates + demo meetings **every two weeks**. Response SLA: **8 working hours, PH business days (Mon–Fri 09:00–18:00 PHT, excluding PH holidays)**. This stands for professionalism and official records; compromise is allowed when highly needed — resolving downtime or unblocking the client's own clients.
- **Client delays:** a **hard blocker** (a client-side requirement with no workaround and no other tasks possible without it) unresolved for more than 24 hours extends the deadline **1:1** with the delay.

---

# 3. Engineering practice

## 3.1 Repositories

- **Monorepo per client project.** Subsystems (data pipeline, second backend for microservices) live inside the same monorepo. A new monorepo requires a genuinely independent project.
- Standard skeleton: `apps/` (web, api) · `packages/` (shared types/clients) · `pipelines/` (ingestion/Dagster) · `infra/` (deploy config, IaC) · `docs/` (pinned constitution, `adr/`, runbook) · `e2e/` (Cypress). Tooling: pnpm workspaces (TS) + uv (Python).

## 3.2 Branching & merging

- **Trunk-based.** Short-lived feature branches off `main`; PR required; **self-merge allowed with CI green**; squash merge; conventional commits (`feat:` `fix:` `chore:` …). `main` is protected against direct pushes and is always releasable.
- **No per-environment branches and no auto-deploy from `main`.** There is a single deployment at any time (§3.5), promoted deliberately.

## 3.3 CI/CD

- **GitHub Actions** on every repo: pre-commit checks, lint, type-check, unit, integration, e2e, license gate (§3.7).
- Deployment is a deliberate, manual promotion — not a pipeline side effect.

## 3.4 Testing floor & Definition of Done

- Floor on every project: **pre-commit hooks + unit tests + integration tests + Cypress e2e per user flow including edge cases** (component tests ride with e2e) + a **final manual test by the developer per ticket**.
- A ticket is **Done** when: acceptance criteria met · CI green · **proof-of-test posted in the ticket comments — a video recording or screenshots following the manual step-by-step test instructions exactly as the client would perform them** · docs/runbook updated if behavior changed.
- A phase is **Done** when all tickets are Done and the phase is demoed.

## 3.5 Environments — single-environment lifecycle

- **Only one deployed environment exists at any time.** Most development happens locally.
- **Pre-MVP / pre-production phases:** deploy a **testing environment** to the cloud — free where the platform's terms allow — strictly for the client's internal testing. It never serves real users. Workloads that cannot deploy free (Windows-VM services, long-running processes, heavy pipelines) are out of free-deploy scope → escalate as a client decision.
- **Production-targeting phase:** building the **AWS cloud infrastructure is in that phase's scope**. On cutover the environment becomes production and the old testing environment is torn down.
- **Hosting rule: testing environment = Vercel free tier (FE + BE as serverless functions); production = always AWS. Railway (and any other third PaaS) is not used — Hetzner is the only alternative, and exclusively for EU data residency (§5.1). No third PaaS.**
  - Vercel free BE constraints (validated 2026-07): 60s max function duration (300s with Fluid compute), 4h active CPU/month — fine for CRUD APIs and record-and-respond agent turns; **not viable** for Dagster, WebSockets, or long-running jobs (those escalate per above; pipelines may run locally/on-demand pre-production).
  - Accepted risk on record: Vercel Hobby's ToS prohibits commercial use and Vercel may remove deployments without notice. Internal-testing deploys are a gray zone we accept; if Vercel objects, fallback is client-paid Pro, escalated per §7.2.
  - **Never rotate accounts or emails to extend any platform's trial.** ToS breach, ban risk mid-engagement, and it contradicts client-pays.
- **Account ownership (testing env):** RSPH owns the third-party accounts (deploy, tracing, monitoring) since they are easily replaced — **except the database**: the client creates their own org (e.g. Supabase) and invites RSPH, or shares credentials if the free tier can't invite. RSPH pays for nothing; anything unpayable-for-free escalates to the client.

## 3.6 Coding standards

- Python: **uv + ruff (lint & format) + mypy** on new code. TypeScript: **strict mode + eslint + prettier**.
- Frontend↔backend data layer: **TanStack Query on every project** — normalizes fetching and provides built-in caching.
- API: FastAPI with auto-generated **OpenAPI as the contract**; single JSON error envelope `{code, message, details}`.
- DB migrations: committed to the repo via the migration CLI (e.g. Supabase CLI). Dashboard-only schema changes are prohibited.

## 3.7 Dependencies & license gate

- Renovate (or Dependabot) on every repo, weekly batched PRs, self-merged on CI green.
- **License gate in CI:** builds fail if shipped product code embeds SUL-, BUSL-, or AGPL-licensed components. This automates the workflow-platform ban and prevents the next licensing surprise.

## 3.8 Secrets

- Runtime mechanism: `.env`, git-ignored, held by RSPH; credentials provided by the client.
- **Source of truth: Bitwarden free 2-user organization** (validated 2026-07: free plan includes a 2-user org with shared collections). All client creds + RSPH keys live there; `.env` is generated from it; credentials never travel through chat or email; rotate everything at handover and whenever anyone's access ends. Alternative if automated per-project env syncing is later wanted: Infisical (free ≤5 identities, MIT self-host).

## 3.9 AI-augmented development

- Every repo ships a **`CLAUDE.md`** that references the pinned constitution and project conventions, so every AI session inherits the rules.
- AI-generated code passes the same CI and the same per-ticket manual test as human code. **No AI-generated diff merges without the developer having read it** — CI green alone is not review.
- Beyond this, the standing prompt template governs AI usage.

---

# 4. Security & data protection practice

- **AppSec checklist, run twice per project (design + pre-UAT):** OWASP Top 10 + **OWASP LLM Top 10**. Hard rules: parameterized queries only; LLM output is never executed and never interpolated into SQL/HTML unsanitized; agent tools are allowlisted with typed schemas; destructive tools require human confirmation; Cloudflare WAF on by default.
- **Per-tenant rate limits and per-tenant spend caps with a kill switch.** Under client-pays, abuse of a voice/LLM endpoint is direct money loss; TTS is typically ~90% of voice cost.
- **Trace privacy (default stance):** production traces have **PII redaction/data-masking enabled** (e.g. LangSmith masking) with minimal retention; testing env may keep full traces. Client docs always list subprocessors (LangSmith, OpenRouter, Deepgram, ElevenLabs, …). Disable provider prompt-logging where the client requires it.
- **LLM credential store:** provider creds saved in the database with **envelope encryption** — per-tenant data key encrypts creds; master key in the platform KMS (e.g. Supabase Vault); never a bare key in code or `.env`.
- **Backups & DR (documented default, not an SLA):** RPO 24h, RTO best-effort 24h. Daily DB backups (PITR only if the client pays for the tier); weekly automated export of the Markdown source-of-truth + DB dump to a **client-owned** bucket. The vector DB is treated as **rebuildable from the Markdown source of truth** — the rebuild procedure is a mandatory runbook page.
- **Incident response:** SEV1 = prod down / data breach · SEV2 = major feature degraded · SEV3 = minor. Acknowledgment: SEV1 < 4 PH business hours (best effort < 24h any calendar day) · SEV2 < 8 working hours · SEV3 next business day. First move is **rollback, not forward-fix**. SEV1 gets a written postmortem within 5 business days.
- **Personal-data breach:** assess within 24h; notify the NPC and affected data subjects within **72 hours** (statutory, RA 10173). The DPO leads (§9).
- **On-call:** RSPH commits to **no 24/7 coverage under any contract**. SEV1 response < 24h any calendar day; everything else per the working-hours SLA. During hypercare (§7.4): elevated to < 4h, 09:00–18:00 PHT.

---

# 5. Standard architecture defaults

## 5.1 Universal defaults (every project type)

| Layer | Default | Notes |
|---|---|---|
| Frontend | **React / Next.js (TS)** • **TanStack Query** | Branded web app on every project. |
| Backend | **FastAPI** (Python) | OpenAPI contract; standard error envelope. |
| Data / Auth / Storage | **Supabase** (Postgres · Auth · Storage) | RLS by tenant; client-owned org from day one (§3.5). |
| Hosting | **Vercel free (testing env, FE+BE) → AWS (production, always)** | Cloudflare DNS/WAF. Hetzner only for EU data residency. **No Railway / third PaaS.** No K8s (§1). |
| CI/CD | GitHub Actions | §3.3. |
| Error monitoring | **GlitchTip** (Sentry-SDK compatible) | Hosted $15/mo billed to client, or self-host (~2GB instance) on client infra; FE+BE SDKs from phase 1. Ultralight alternative: Bugsink. |
| Uptime | **Better Stack free** (10 monitors, 3-min, status page) | One account per client. UptimeRobot excluded — free plan is non-commercial since early 2026. |
| Integrations | **Direct API integrations in the backend** | Workflow platforms (n8n/Zapier/Make) banned from products; PoC only (§1). |
| Non-AI products | Apply this table + §3–§4 + §6–§10 | The AI/RAG table below simply doesn't attach. Higher-level guidance: same principles, same delivery model, same compliance. |

## 5.2 AI/RAG product defaults

| Layer | Default | Notes |
|---|---|---|
| Agent orchestration | **LangGraph** (in-process) | Real-time agent as a stateful graph; no webhook hop. |
| Retrieval | **LangGraph subgraph, Strategy pattern** | Two swappable strategies: (1) hybrid (BM25 sparse + dense, Milvus-native); (2) hybrid + re-ranking (SLM/cross-encoder). Same output shape; swap per query/tenant. New strategies = new class, not a refactor. |
| Ingestion / data pipeline | **Dagster** (self-host OSS), two jobs | Job 1: source-specific extractors → normalized Markdown → object storage (citation source of truth). Job 2: chunk + embed → vector DB. Pre-production: run locally/on-demand (won't fit Vercel serverless); managed deploy arrives with the AWS production phase. |
| Source parsing | **Docling** · Notion API · YouTube transcript → Whisper fallback | Each source handled its own way; everything normalized to Markdown. Docling = PDF/files → Markdown. |
| Vector DB | **Milvus (Zilliz Cloud)** — always for real builds | HNSW; tenant partitions; content + memory collections; native hybrid (BM25 + dense). **pgvector is permitted for testing/PoC only** — using it further just buys a redundant migration to Milvus later. |
| Model access | **LLM factory: provider-agnostic adapter** | Default OpenRouter; **Nebius as fallback**; any provider connectable. Creds stored encrypted in DB (§4); provider/model/creds config surfaced in the **operator / super-admin UI** so the client self-serves and RSPH maintenance approaches zero. |
| Model tiering | **SLM + Claude** | SLMs for intermediate single-responsibility tasks (rewrite, re-rank, guardrails, unknown-query detection, memory extraction); Claude for the user-facing agent (Haiku default, Sonnet for hard turns). |
| Embeddings | **No fixed model name — per-project choice** | Choose the cheapest current-gen model that passes retrieval evals for the project's situation. Must stay consistent within a project; **changing the model requires re-embedding all existing vectors.** |
| Memory | **LangGraph store + LangMem** — default placeholder, evaluated per project | Works for PoC/MVP stage. Caveat: LangMem is pre-1.0 with a slow release cadence; fallback is plain LangGraph BaseStore + custom extraction prompts. No Mem0 (crippled OSS + relicensing risk). |
| Tracing | **LangSmith** | Prod: PII masking on (§4). |
| STT | **Deepgram** | Python SDK, streaming, low latency. Whisper/gpt-4o-transcribe = ingestion fallback only. |
| TTS | **ElevenLabs Flash + Professional Voice Cloning** | Voice cloning is the deciding factor. Cartesia (Sonic) = cost-lever alternative (~1/5 the per-minute price). Ruled out: preset-voice-only engines. |
| Chat transport | **AG-UI protocol over SSE only** | Client→server via HTTP POST; server→client via SSE; no WebSocket in MVP. Two input flows: text posts direct to the agent; voice = record → server-side STT (STT optional, not a hard dependency). WebSocket/WebRTC only for continuous live-call/barge-in — which also forces the hosting exception in §3.5. |

**Tool-selection criterion (STT/TTS/etc.):** must run in Python with an SDK/library, or interact via a fully-featured, non-limited API.

## 5.3 RAG design patterns

- **Retrieval behind a Strategy interface** — ship the two strategies above; further strategies (graph, multi-query) slot in as new classes.
- **Ingestion in two jobs** with normalized Markdown in object storage as the citation source of truth (and the DR rebuild source, §4).
- **Citations:** metadata (section, timestamp, char offsets) + raw Markdown retained in Storage → exact-span, auditable citations.
- **Knowledge-gap loop (HITL flywheel):** unknown queries → stored in DB → operator answers in the UI → answer embedded into the KB (+ memory).
- **Guardrails/escalation** via an SLM; log out-of-KB queries as "missing information."
- **Latency target:** voice **p95 < 3 s end-to-end** measured user-stops-speaking → first audio; text **p95 first token < 1.5 s**. Stream everything; prompt caching; cap context to 5–10 chunks; cache TTS audio for FAQs.

## 5.4 AI evaluation — adaptive framework (Phase 2, post-MVP)

Any AI system that produces user-facing generative output and requires evaluation follows a data-flywheel eval discipline, **sized to the system and its risk**. A **RAG or large-agent product → the full framework**. A **smaller / leaner AI system (e.g. a deterministic-backed narrator with no retrieval) → the lean tier**. Guiding principle: *where a deterministic source of truth exists, make the correctness check deterministic and reserve LLM-as-judge / golden-sets for the softer qualities.*

**Full framework (RAG / large AI systems).**

- **Trigger: non-optional once a RAG product has been in production 30 days, and before any prompt/model change ships to prod** (regression gate).
- Monthly evaluation pipeline (Ragas / DeepEval + LangSmith): faithfulness/groundedness, context precision & recall, answer relevancy/correctness, persona adherence, escalation correctness, latency; Dagster-scheduled.
- On-demand SDG pipeline: synthetic Q&A from the KB → pending goldens → **required human review** → final goldens.
- Conversation → dataset curation; feedback capture (thumbs); retrieval-V2 A/B measured by evals; SLM distillation from curated data; analytics + regression/latency alerting.

**Lean framework (small / non-RAG AI systems — e.g. a deterministic-backed narrator).**

- **Deterministic faithfulness first.** Where a deterministic engine / source of truth exists, enforce output↔truth agreement as a **deterministic assertion** (parse the output, compare every number / fact / rule-state to the source, fail on mismatch) — no judge model needed for the core correctness guarantee.
- **Synthetic-silver → operator-gold flywheel.** Seed a small golden set via DeepEval SDG; capture user thumbs in the DB; flagged-bad outputs enter a **pending dataset**; an **operator supplies the expected answer**; on save it promotes to the **golden dataset** (tagged with source + version). Route a small **random production sample** (not only flagged items) for operator review to avoid blind spots.
- **Two cadences:** run the golden set as a **pre-deploy regression gate** (before any prompt / workflow change ships) **and** on a **monthly** trend cadence. Soft qualities (tone, clarity, action sensibility) use LLM-as-judge; hard correctness stays deterministic.
- **Improve via prompt / workflow optimization, not model fine-tuning** (Prompt → RAG → Fine-tune → Distill). Model fine-tuning is reserved for a *measured* gap prompting cannot close.
- Eval runtime costs are platform costs → client pays (§7.2).

---

# 6. Cost model conventions

- Show **USD and PHP** (re-check and cite the FX rate + date each time).
- Separate **one-time vs recurring (monthly)**; list **usage-based unit rates** with sources.
- Compute **unit economics**: per conversation/request, per 1,000, per active tenant/month, and implied margin at a given price. Name the dominant cost driver and its levers.
- **Production cost guardrails (mandatory at go-live):** provider-native budget alerts on every client account (OpenRouter spend limit, Supabase spend cap, AWS budget alerts, ElevenLabs quota) + a weekly automated cost digest to client and RSPH.
- Foreseeable platform line items (e.g. AWS at the production phase) go into the proposal cost model so they're approved at proposal stage, not mid-build.

---

# 7. Commercials & engagement

## 7.1 Pricing & payment

- **Fixed, project-based pricing** (per build). Future work = additional fixed builds or the retainer (§7.5).
- Payment via **Deel milestone escrow**. Milestone payments made are non-refundable.
- RSPH has its own **MSA/SOW templates**; liability is capped at total fees paid under the SOW, excluding indirect/consequential damages *(have PH counsel sanity-check once; not legal advice)*.

## 7.2 Who pays what

- **Client pays all platform/API subscriptions and usage** (OpenRouter, Deepgram, ElevenLabs, Zilliz, Supabase, AWS, monitoring, eval runs, …). RSPH pays for nothing at runtime; free tiers are used only where terms permit; anything unpayable-for-free escalates to the client as an explicit decision.
- **The tech stipend covers RSPH development tooling only** (Claude subscriptions, dev tools) — never the project's runtime platform costs.

## 7.3 IP

- **Client owns the bespoke code** built on top of the template. **RSPH owns the template.** The template embedded in a deliverable is licensed to the client **perpetual, non-exclusive, non-transferable, for that product only**; RSPH reuses the template freely across clients.
- A **client-owned template** is a separate project with its own fixed fee, priced to the client's standards. Never fold it into a product build fee, and never reuse a proprietary internal template on a build where the client is to own the template.

## 7.4 Warranty, hypercare, handover

- After final sign-off: **7-day hypercare** (elevated response, §4) followed by a **30-day warranty** — defect fixes free; 37 days of coverage total. After warranty, model/provider swaps and changes are billed (smallest CR class for adapter-backed model swaps).
- **Standard handover package**, delivered as a `handover/` folder in the repo: repo transfer + admin rights · full credential rotation + vault handoff · final TDD (as-built) · runbook (deploy, rollback, backup/restore, vector-DB rebuild, common ops) · operator/admin guide (incl. the LLM-factory config UI) · OpenAPI docs · env-var inventory · cost dashboard + alerts walkthrough · one recorded walkthrough video + one live Q&A session · warranty terms one-pager.
- **Tenant/client offboarding:** scripted, tested deletion (vector partitions → Postgres cascade → Storage purge → traces), 30-day export grace, written deletion confirmation on request.

## 7.5 Retainer & change requests

- A **standard retainer offering exists**: fixes and support are covered; anything requiring new development is billed in phases by complexity and estimated weeks.
- **Change requests: written CR + fixed quote + client sign-off before any work.** No exceptions.

## 7.6 Kill / pause / subcontracting

- Client unresponsive > 10 business days → project auto-pauses; restart scheduled per RSPH availability.
- Invoice unpaid > 15 days past due → work stops until settled.
- **No subcontracting without prior written client consent** (also keeps NPC outsourcing compliance trivial).

## 7.7 Service levels

- **No contractual SLA without a retainer.** Published non-binding **service objectives**: 99.5% monthly uptime (inherited from the platforms), voice p95 < 3s, text p95 first-token < 1.5s. With a retainer, RSPH sells **response-time** commitments (§4), never uptime.
- **Model deprecation:** provider deprecation notices are checked monthly; swaps within warranty are free, after warranty a small CR — the adapter + evals make this cheap, and client docs say so.

---

# 8. Document conventions

- Three internal docs per project: **Project Overview** (comprehensive) · **Technical Design Document** (architecture + cost + unit economics) · **Technical Implementation Plan** (phased, parallel-lane).
- Options comparisons scored 1–5 with a shaded recommended row + a recommendation tied to the constraints. Assumptions + Open Questions in every doc. Tables for structure; prose for trade-offs; research-first with cited, dated sources.
- **Versioning:** the version increments in the document name/header only. The body contains no version-comparison commentary or original-brief traceability — deltas belong in the accompanying report/changelog. Documents stay clean.
- **Two audiences, two versions.** Internal docs are comprehensive; sharing with the client requires a `*_client` version. **Redaction checklist** (mechanical, every time): strip internal effort/hours · margins/COGS · the parallelization split · internal delivery risks · scored decision tables. Keep: architecture, value, security/privacy, timeline, "what we need from you."

---

# 9. Compliance

- **PH Data Privacy Act (RA 10173) attaches to the processor, not the hosting region.** It applies to RSPH as a Philippine-established processor even when the product resides in the US. Never treat "US region" as an exemption. (Nuance: the exact reach over a PH processor handling only foreign data is debated; the prudent baseline is DPA-grade processing regardless.)
- **Both layers apply independently:** separately from RA 10173, the product follows the data subjects' own jurisdiction — US clients → US region + applicable US privacy law (client = controller); EU clients → EU data residency (AWS EU / Hetzner) + GDPR.
- **DPO is mandatory for every PIC/PIP — RSPH's DPO is Kai.** Duties: monitor DPA/IRR/NPC compliance · run a **Privacy Impact Assessment per project** (1-page template) · named contact for data-subject requests · lead breach response (72-hour clock, §4) · liaise with the NPC · keep records of processing · annual privacy briefing. The DPO must be organic to RSPH (PH does not allow outsourced DPOs) and reports to the founders.
- **NPC registration (Circular 2022-04) is threshold-based:** required at 250+ employees, OR sensitive personal information of 1,000+ individuals, OR risky processing, OR **any automated decision-making/profiling — regardless of company size**. Below thresholds: file the sworn declaration via the NPC registration system. *(Action item: RSPH's filing is pending as of 2026-07.)*
- **ADM/profiling screen at every project kickoff** (any "yes" → register that data processing system with the NPC + disclose in the privacy notice + add a human-review mechanism):
  1. Does the system make or materially inform decisions about identifiable individuals?
  2. Without meaningful human review?
  3. Does it profile individuals' behavior or preferences (scoring, screening, ranking people)?
  A typical RAG Q&A assistant → all "no". A resume screener, loan scorer, or lead-scoring-on-individuals feature → "yes".

---

# 10. Per-project client inputs (always required)

Collect at project start; list under "what we need from you" / Open Questions:

- **Brand assets** — logo, colours, brand guidelines. Every project ships a branded web app.
- **Content / data access** to whatever powers the product (sources, exports, API access).
- **Platform accounts + billing** — the client's database org (e.g. Supabase) from day one; the client's AWS account before the production-targeting phase; billing for all runtime services (§7.2).
- **Consent + samples for anything sensitive** — e.g. a clean voice sample and written cloning consent for voice cloning.
- **A named approver** for sign-off and HITL review (e.g. knowledge-gap answers).
- **Seed domain knowledge** — 20–50 seed Q&A pairs / a domain glossary to bootstrap the golden dataset (RAG projects).
- **A named data-deletion contact** and confirmation of which subprocessors the client accepts (§4 disclosure list).

---

# 11. Decision log (concrete calls that recur, each with its revisit condition)

| Decision | Revisit when |
|---|---|
| Milvus over pgvector for anything real; pgvector = testing/PoC only | Milvus/Zilliz pricing or license changes materially |
| LLM factory: provider-agnostic adapter; OpenRouter default, Nebius fallback; creds encrypted in DB; config in operator UI | A client requires direct-provider contracts or data residency the adapters can't route |
| No fixed embedding model; per-project choice; change ⇒ full re-embed | Never — this is a policy, not a pick |
| SLM + Claude model tiering | Claude pricing/tiering changes; SLM quality closes the gap on the user-facing turn |
| LangGraph for agent + retrieval subgraph; Dagster for ingestion (two jobs) | Either project's governance/license shifts; team size changes the ops calculus |
| Workflow platforms (n8n/Zapier/Make) banned from products; PoC only; MVP only on informed client insistence | A platform ships a genuinely OSS, embeddable license |
| LangGraph store + LangMem as memory placeholder, evaluated per project; Mem0 rejected | LangMem hits 1.0 / goes unmaintained |
| Raw Markdown in object storage = citation source of truth + DR rebuild source | Never — load-bearing pattern |
| Deepgram STT / ElevenLabs Flash + PVC; Cartesia as cost lever | Voice cloning stops being the deciding factor; price moves >2× |
| AG-UI over SSE, no WebSocket in MVP; two input flows (text-direct / voice-via-STT) | Continuous live-call/barge-in enters MVP scope |
| Docling + source-specific extractors, everything normalized to Markdown | A source type Docling can't handle becomes common |
| TanStack Query as the FE↔BE data layer | Never within React ecosystem; revisit only on framework change |
| Testing env on Vercel free (FE+BE); production always AWS; **Railway / other PaaS not used** (Hetzner only for EU residency); single environment; no account rotation | Vercel enforces Hobby commercial terms against a testing deploy; project needs un-serverless-able workloads earlier |
| GlitchTip (Sentry-SDK) + Better Stack free monitoring | Client already pays for a monitoring stack; GlitchTip hosted pricing changes |
| Bitwarden free 2-user org as secrets source of truth | Team grows past 2; Bitwarden drops the free org |
| Template = RSPH-owned, licensed per product; client-owned template = separate priced project | Never — core commercial position |
| Client pays all platform costs; stipend = RSPH dev tools only | Never — core commercial position |
| 60/40 parallel lanes; (N−1) build weeks + 1 UAT week | First hire changes the lane math |
| Phase 2 evals mandatory after 30 days in prod for RAG products | Never — production-grade discipline |
| Internal + `*_client` doc versions with redaction checklist | Never |
| No K8s / self-managed clusters; managed/serverless by default; K8s only as separate paid engagement | A client's hard requirement forces it (then: separate engagement) |
| No 24/7 on-call, ever; no SLA without retainer; response-time (not uptime) commitments | Never |
