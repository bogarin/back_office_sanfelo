---
name: documentation-generation
version: "1.0.0"
description: Generates structured documentation for Backoffice Trámites project using Diátaxis framework
---

# Documentation Generation Skill

Generate structured documentation following Diátaxis framework with Spanish content.

## Documentation Structure

```
docs/
├── 01-onboarding/     # Project overview, glossary, architecture
├── 02-tutorials/      # Step-by-step learning by role
│   ├── operators/
│   ├── admins/
│   └── developers/
├── 03-guides/         # Problem-solving guides by role
├── 04-concepts/        # Theoretical explanations
├── 05-reference/       # Technical reference (SSOT)
├── 06-decisions/       # Architecture Decision Records
├── 07-maintenance/     # Release notes, upgrades
└── 08-ai-optimized/  # LLM-optimized content
```

## Document Types

### Tutorials
- Purpose: Learning by doing
- Audience: Beginners, new team members
- Structure: Steps with expected outcomes
- Location: `02-tutorials/{role}/`
- Template: `docs/_templates/tutorial-template.md`

### Guides (How-to)
- Purpose: Solving specific problems
- Audience: Experienced users
- Structure: Prescriptive instructions
- Location: `03-guides/{role}/`
- Template: `docs/_templates/guide-template.md`

### Concepts
- Purpose: Explaining "why"
- Audience: Understanding context
- Structure: Theoretical with diagrams
- Location: `04-concepts/`
- Template: `docs/_templates/concept-template.md`

### Reference
- Purpose: Technical details
- Audience: Developers, Sysadmins
- Structure: Tables, parameters, examples
- Location: `05-reference/`
- Template: `docs/_templates/reference-template.md`

## User Roles

### Operators (非-technical)
- Language: Simple, no jargon
- Focus: Tasks and results
- NO: Python, Django, database, code
- YES: UI screenshots, business examples

### Administrators (非-technical)
- Language: Simple, task-focused
- Focus: Django Admin usage, configuration
- NO: Code implementation details

### Developers (technical)
- Language: Technical jargon appropriate
- Focus: Implementation, architecture, API
- YES: Code examples, Django docs links
- NO: Basic Python/Django concepts (assumed knowledge)

### Sysadmins (technical)
- Language: Ops-focused
- Focus: Deployment, monitoring, troubleshooting
- YES: Complete copy-paste commands
- NO: Business logic explanation

### AI/LLM Agents
- Structure: Semantic H1-H6 headings
- Format: Clear, unambiguous
- Include: JSON schemas, executive summaries
- NO: Metaphors, humor, sarcasm

## Content Principles

### SSOT (Single Source of Truth)
Each fact lives in ONE location. Others reference it.

### Progressive Disclosure
Summary → Detail → Depth. 3 levels of explanation.

### Andragogy
- Immediate: Info when needed now
- Relevant: Why it matters (WIIFM)
- Practical: Real problems, not abstract theory
- Autonomous: Self-guided exploration

### Minimal Documentation
Document only what's necessary. Don't document Django/Python basics.

## Templates Location

- Tutorial: `docs/_templates/tutorial-template.md`
- Guide: `docs/_templates/guide-template.md`
- Concept: `docs/_templates/concept-template.md`
- Reference: `docs/_templates/reference-template.md`

## Workflow

1. Identify document type (Tutorial/Guide/Concept/Reference)
2. Select appropriate template
3. Write in Spanish
4. Follow Diátaxis framework
5. Check for duplicates before creating
6. Update docs/README.md if needed


## Metrics

- README.md target: ~150 lines (from 494)
- Target: 0% duplicate content
- Language: 100% Spanish
- SSOT: One location for each fact
