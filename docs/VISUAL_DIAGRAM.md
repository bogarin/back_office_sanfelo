# Documentation Structure - Visual Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKOFFICE TRÁMITES DOCUMENTATION                    │
│                           New Proposed Structure                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   README.md      │  ◄───────────────────┐
│  (Landing Page)  │                      │
└────────┬─────────┘                      │
         │                               │
         │ Role Selection                │
         ▼                               │
    ┌────────────────┐                   │
    │  5 Quick Start │                   │
    │     Links      │                   │
    └────┬─────┬────┘                   │
         │     │                        │
   ┌─────┘     └────────┐               │
   │                      │               │
   ▼                      ▼               │
┌─────────┐          ┌─────────┐         │
│Operator │          │Developer│        │
│         │          │         │        │
└────┬────┘          └────┬────┘        │
     │                    │              │
     ▼                    ▼              │
┌───────────────────────────────────────┴──────────────────────┐
│                        docs/ Directory                         │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 01-onboarding/                      🚀 New Members    │   │
│  │   ├── overview.md                  (All Roles)        │   │
│  │   ├── glossary.md                                      │   │
│  │   └── architecture-overview.md                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 02-tutorials/                      📖 Step-by-step    │   │
│  │   ├── operators/                    (Learning)        │   │
│  │   │   ├── create-tramite.md                          │   │
│  │   │   └── manage-workflow.md                         │   │
│  │   ├── admins/                                       │   │
│  │   │   ├── setup-users.md                            │   │
│  │   │   └── manage-catalogs.md                        │   │
│  │   └── developers/                                    │   │
│  │       ├── local-dev-setup.md                        │   │
│  │       └── first-api-call.md                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 03-guides/                         📋 Problem-Solving│   │
│  │   ├── operators/                    (By Role)         │   │
│  │   ├── admins/                                       │   │
│  │   ├── sysadmins/                                    │   │
│  │   └── developers/                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 04-concepts/                       🧠 Theory          │   │
│  │   ├── dual-database.md             (Why & How)        │   │
│  │   ├── no-migrations.md                                │   │
│  │   ├── denormalization.md                             │   │
│  │   ├── caching-strategy.md                            │   │
│  │   ├── auth-system.md                                 │   │
│  │   └── audit-system.md                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 05-reference/                      📖 Technical       │   │
│  │   ├── api/                           (SSOT)           │   │
│  │   ├── models/                                         │   │
│  │   ├── commands/                                       │   │
│  │   ├── configuration/                                  │   │
│  │   └── components/                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 06-decisions/                      📋 ADRs            │   │
│  │   ├── README.md                     (Architecture)    │   │
│  │   ├── 001-stack-base.md                               │   │
│  │   ├── 002-dual-database.md                            │   │
│  │   └── ...                                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 07-maintenance/                    🔧 Operations      │   │
│  │   ├── release-notes.md               (Updates)        │   │
│  │   ├── upgrade-guide.md                                 │   │
│  │   ├── changelog.md                                    │   │
│  │   └── security-advisories.md                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 08-ai-optimized/                   🤖 LLM-Ready       │   │
│  │   ├── context.md                     (AI Agents)      │   │
│  │   ├── architecture-summary.md                          │   │
│  │   ├── code-patterns.md                               │   │
│  │   └── api-spec-json.md                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │Success │          │Success │          │Success │
    │        │          │        │          │        │
    └─────────┘          └─────────┘          └─────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        USER PATHS (DETAILED)                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ OPERATOR PATH (Daily Usage)                                 │
│                                                              │
│ README.md ──► create-tramite.md ──► manage-workflow.md      │
│    │              │                   │                     │
│    │              └──► change-status.md                     │
│    │                  └──► upload-docs.md                   │
│    │                      └──► search-tramites.md           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ADMINISTRATOR PATH (System Configuration)                   │
│                                                              │
│ README.md ──► setup-users.md ──► manage-catalogs.md          │
│    │              │                   │                     │
│    │              └──► add-peritos.md                       │
│    │                  └──► configure-costs.md               │
│    │                      └──► manage-groups.md              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DEVELOPER PATH (Full Technical)                             │
│                                                              │
│ README.md ──► architecture-overview ──► local-dev-setup       │
│    │              │                      │                  │
│    │              └──► first-api-call    └──► guides/*       │
│    │                      │                 (as needed)      │
│    │                      └──► concepts/*                     │
│    │                          (as needed)                    │
│    │                      └──► reference/*                   │
│    │                          (as needed)                    │
│    │                      └──► decisions/*                   │
│    │                          (as needed)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SYSADMIN PATH (Operations)                                  │
│                                                              │
│ README.md ──► deploy-production ──► docker-setup              │
│    │              │                   │                     │
│    │              └──► backup-restore ──► monitoring          │
│    │                  │                   │                  │
│    │                  └──► troubleshoot ──► reference/*       │
│    │                                          (as needed)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ AI AGENT PATH (LLM-Optimized)                               │
│                                                              │
│ 08-ai-optimized/context.md ──► architecture-summary.md        │
│        │                      │                             │
│        └──► api-spec-json.md  └──► decisions/*              │
│            (JSON parsing)          (as needed)               │
│                                    │                         │
│                                    └──► concepts/*           │
│                                        (as needed)           │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION FLOW (Diátaxis)                       │
└─────────────────────────────────────────────────────────────────────────┘

TUTORIALS                GUIDES                    CONCEPTS              REFERENCE
   │                       │                          │                      │
   ▼                       ▼                          ▼                      ▼
┌─────────┐           ┌─────────┐               ┌─────────┐          ┌─────────┐
│ Learning│           │Solving  │               │Understanding│      │Looking up│
│ by doing│           │problems│               │   "why"  │          │  facts  │
│         │           │         │               │          │          │         │
│ - Create│           │ - Change│               │ - Dual DB│          │ - API   │
│   first │           │   status│               │ - No     │          │   specs │
│   tramit│           │ - Upload│               │   migrations│        │ - Env   │
│ - Setup │           │   docs  │               │ - Cache  │          │   vars  │
│   users │           │ - Deploy│               │ - Auth   │          │ - Models│
└─────────┘           └─────────┘               └─────────┘          └─────────┘
   │                       │                          │                      │
   │ Progressive Disclosure│                          │                      │
   └───────────────────────┴──────────────────────────┴──────────────────────┘
                                    │
                                    ▼
                           ┌───────────────┐
                           │   Single Source│
                           │     of Truth   │
                           └───────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        KEY PRINCIPLES                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PROGRESSIVE DISCLOSURE                                        │
│                                                              │
│ Level 1: Quick Summary (3 seconds)                          │
│   ↓                                                          │
│ Level 2: Basic Info (1-2 minutes)                           │
│   ↓                                                          │
│ Level 3: Deep Dive (as needed)                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SINGLE SOURCE OF TRUTH (SSOT)                                │
│                                                              │
│ ❌ BEFORE (Duplication):                                     │
│   README.md ──┬── "uv run python manage.py runserver"      │
│   COMANDOS_DJANGO.md ─┘                                      │
│   DJANGO_ADMIN_SETUP.md ─┘                                   │
│                                                              │
│ ✅ AFTER (SSOT):                                              │
│   commands/index.md ── "uv run python manage.py runserver"  │
│      │                                                        │
│      ├── README.md → "See: [Commands]"                       │
│      ├── Tutorials → "See: [Commands]"                       │
│      └── Guides → "See: [Commands]"                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ANDRAGOGY (Adult Learning)                                   │
│                                                              │
│ ✅ Immediate: Information needed NOW                         │
│ ✅ Relevant: Why does this matter to me?                     │
│ ✅ Experience: Build on existing knowledge                   │
│ ✅ Problem-oriented: Solve real problems                     │
│ ✅ Autonomous: Self-guided exploration                      │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                              │
└─────────────────────────────────────────────────────────────────────────┘

Week 1:                    Week 2-3:                   Week 4-5:
┌──────────┐              ┌──────────┐               ┌──────────┐
│PREPARATION│              │EXTRACTION│               │CREATION │
│          │              │          │               │          │
│- Structure│             │- Extract │              │- New    │
│  setup    │             │  from    │              │  content│
│- Guide    │             │  README  │              │- Missing│
│  docs     │             │- Remove  │              │  docs   │
│- Templates│             │  dups    │              │- AI-opt │
└──────────┘              └──────────┘               └──────────┘

Week 6:                    Week 7-8:
┌──────────┐              ┌──────────┐
│  REVIEW  │              │ LAUNCH   │
│          │              │          │
│- Audit   │              │- Publish │
│  dups    │              │  new    │
│- Validate│              │  structure│
│  paths   │              │- Collect │
│- Test    │              │  feedback│
│  nav     │              │- Iterate │
└──────────┘              └──────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    EXPECTED OUTCOMES                                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ QUALITATIVE IMPROVEMENTS                                    │
│                                                              │
│ ⬇ Time to First Value (TTFV): -50%                         │
│ ⬇ Support tickets: -40%                                     │
│ ⬆ Search success rate: +80%                                 │
│ ⬆ User satisfaction: 4.5/5                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ QUANTITATIVE IMPROVEMENTS                                   │
│                                                              │
│ ⬇ README.md: 494 lines → ~150 lines (-70%)                 │
│ ⬇ Duplication: 3+ locations → 1 (SSOT) (-67%)              │
│ ⬆ User paths: 0 → 5 defined (one per role)                 │
│ ⬆ AI-ready docs: 0 → 4 documents                           │
│ ⬇ LLM context tokens: ~5000 → ~1500 (-70%)                 │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    SUCCESS CRITERIA                                      │
└─────────────────────────────────────────────────────────────────────────┘

✅ Documentation Coverage: 100% of files documented
✅ API Completeness: 100% of endpoints documented
✅ Link Integrity: 0% broken links
✅ Freshness: 80% updated in last 3 months
✅ User Satisfaction: 4.5/5 (each role)
✅ AI Performance: Reduced context, higher accuracy
```

---

*This visual diagram illustrates the proposed documentation restructuring plan. For complete details, see [RESTRUCTURING_PLAN.md](../RESTRUCTURING_PLAN.md) and [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md).*
