# Documentation Methodologies - Quick Reference

> **Cheat Sheet for the Backoffice Trámites Team**
> Version: 1.0 | Date: February 26, 2026

---

## 📚 Methodologies Overview

This card summarizes the key methodologies we're using to restructure our documentation.

---

## 1. Diátaxis Framework

**What it is**: 4-category documentation structure by Daniel Nathans.

**The 4 Categories**:

| Category | Purpose | Audience | Example |
|----------|---------|----------|---------|
| **Tutorials** | Learning by doing | Beginners | "Create your first tramite" |
| **How-to Guides** | Solving problems | Experienced users | "Change tramite status" |
| **Explanation** | Understanding "why" | Those who need context | "Why dual database?" |
| **Reference** | Looking up facts | Technical users | "API endpoints complete" |

**Key Insight**: Each document serves ONE purpose, not multiple.

---

## 2. Progressive Disclosure

**What it is**: Reveal information gradually based on need.

**The 3-Level Rule**:

```
Level 1: Quick Summary      (3 seconds)
   ↓ "Tell me more"
Level 2: Basic Information  (1-2 minutes)
   ↓ "I need details"
Level 3: Deep Dive          (as needed)
```

**Example for Dual Database**:

Level 1: "We use two databases: SQLite for auth, PostgreSQL for business data."

Level 2: "SQLite stores Django's built-in data (users, sessions). PostgreSQL stores all business data (tramites, catalogos). This separation allows Django to manage its internal data independently from business data managed by an external team."

Level 3: [Full explanation with architecture diagrams, ADR references, etc.]

**Principle**: Don't overwhelm users. Let them dig deeper when they need to.

---

## 3. Information Architecture

**What it is**: Organizing content to be discoverable and navigable.

**Our Principles**:

| Principle | What it means | How we apply it |
|-----------|---------------|-----------------|
| **Task-based navigation** | Organize by what users DO, not by technology | "How to deploy" not "Docker configuration" |
| **User-centered design** | Structure according to user roles | Separate sections for each role |
| **Search-first design** | Make it searchable (for humans AND LLMs) | Clear headings, H1-H6 hierarchy |
| **Semantic structure** | Machine-readable structure | Proper heading levels for parsing |

**Result**: Users find what they need in 3 clicks or less.

---

## 4. Single Source of Truth (SSOT)

**What it is**: Each fact lives in ONE place. Everything else is a reference.

**Current Problem**:

```bash
# This command appears in 3 places:
uv run python manage.py runserver

# Locations:
# - README.md (line 181)
# - docs/COMANDOS_DJANGO.md (line 350)
# - docs/DJANGO_ADMIN_SETUP.md (line 200)
```

**SSOT Solution**:

```bash
# Lives in ONLY ONE place:
docs/05-reference/commands/index.md

# All other files just reference it:
# - README.md: "See: [Commands Reference](docs/05-reference/commands/index.md)"
# - Tutorials: "See: [Commands Reference](docs/05-reference/commands/index.md)"
# - Guides: "See: [Commands Reference](docs/05-reference/commands/index.md)"
```

**Benefits**:
- ✅ No contradictions
- ✅ Easier to maintain
- ✅ No update synchronization issues

---

## 5. Document-Driven Design (DDD)

**What it is**: Document before/during development, not after.

**Our Workflow**:

```
1. Define Requirement
   ↓
2. Write ADR (Architecture Decision)
   ↓
3. Write API Spec (for endpoints)
   ↓
4. Write Reference Documentation
   ↓
5. Implement Code
   ↓
6. Create Tutorials/Guides
```

**Key Insight**: Documentation is part of the development process, not an afterthought.

---

## 6. Andragogy (Adult Learning)

**What it is**: Education principles for adult learners.

**Key Principles**:

| Principle | Meaning | Application |
|-----------|---------|-------------|
| **Immediacy** | Need information NOW | No lengthy intros; get to the point |
| **Relevance** | Why do I care? | Start with WIIFM (What's In It For Me) |
| **Experience** | Build on existing knowledge | Assume Django knowledge for developers |
| **Problem-oriented** | Solve real problems | Focus on tasks, not theory |
| **Autonomy** | Self-guided exploration | Provide paths, don't enforce sequences |

**Example**:

❌ **Bad** (violates andragogy):
```markdown
Django is a high-level Python web framework... It follows the MVT pattern...

Before you can use this system, you need to understand:
1. Python basics
2. Django models
3. Database relationships
...

Now let's talk about how to create a tramite.
```

✅ **Good** (andragogy):
```markdown
## How to Create a New Trámite

This guide shows you how to create a new trámite in the system.

[STEPS TO CREATE TRÁMITE]

**Note**: All trámites must have a valid TipoTramite assigned.
```

---

## 7. Minimal Documentation

**What it is**: Document only what's necessary. Less is more.

**Principles**:

| Do ✅ | Don't ❌ |
|-------|----------|
| Document project-specific decisions | Re-document Django/Python basics |
| Link to official docs | Rewrite what's already documented |
| Explain the "why" | State the obvious |
| Provide business context | List every configuration option |
| Show relevant examples | Show every possible use case |

**Example**:

❌ **Bad** (too much):
```markdown
# Django Settings

Django has a settings file that contains configuration...

The DEBUG setting:
- When True, shows detailed error pages
- When False, shows generic error page
- Must be False in production
- ...
```

✅ **Good** (minimal):
```markdown
# Settings Specific to This Project

## DEBUG
Default: `False`

Set to `True` only in development. In production, always `False`.

## BACKEND_DB_URL
Required: Yes

PostgreSQL connection string for business data.

See [complete settings reference](docs/05-reference/configuration/settings.md)
```

---

## 8. Additional Methodologies

### Technical Writing Best Practices

| Principle | Description |
|-----------|-------------|
| **Active voice** | "Click the button" not "The button should be clicked" |
| **Present tense** | "Click to save" not "Clicking will save" |
| **Clear headings** | Use H1-H6 hierarchically |
| **Lists over paragraphs** | Bulleted lists for options, numbered for steps |
| **Code blocks** | Always show commands in code blocks with syntax highlighting |

### Accessibility (a11y)

| Principle | Application |
|-----------|-------------|
| **Semantic HTML** | Use proper heading structure |
| **Alt text** | Describe images for screen readers |
| **Color contrast** | Ensure text is readable |
| **Keyboard navigation** | Make docs keyboard-accessible |

### LLM Optimization

| Principle | Application |
|-----------|-------------|
| **Structured format** | H1-H6 headings for parsing |
| **Clear syntax** | Unambiguous language |
| **JSON schemas** | API specs in parsable format |
| **Summaries** | Executive summaries at document start |
| **Relationships** | Explicit "see also" links |
| **No ambiguity** | Avoid metaphors, humor, sarcasm |

---

## 🔄 Quick Decision Tree

```
Need to write documentation?
    │
    ▼
What type of content?
    │
    ├─► LEARNING?          ──► Tutorial (02-tutorials/)
    │   "How do I do X?"
    │
    ├─► SOLVING PROBLEM?   ──► Guide (03-guides/)
    │   "I have issue Y"
    │
    ├─► UNDERSTANDING?     ──► Concept (04-concepts/)
    │   "Why Z this way?"
    │
    └─► LOOKING UP?        ──► Reference (05-reference/)
        "What's the spec?"
```

```
Is this information documented already?
    │
    ├─► YES ──► Reference it (don't duplicate)
    │
    └─► NO  ──► Create in appropriate location
```

```
Who is this for?
    │
    ├─► Operator          ──► operators/ (simple, task-focused)
    ├─► Administrator     ──► admins/ (setup and config)
    ├─► Developer         ──► developers/ (technical depth)
    ├─► Sysadmin          ──► sysadmins/ (operations)
    └─► AI Agent          ──► ai-optimized/ (structured, parsable)
```

---

## 📋 Documentation Quality Checklist

Before publishing any documentation, verify:

### Structure
- [ ] Uses Diátaxis category (Tutorial/Guide/Concept/Reference)
- [ ] Located in correct directory (by role)
- [ ] Follows template
- [ ] Has proper H1-H6 heading hierarchy

### Content
- [ ] Single Source of Truth (no duplications)
- [ ] Progressive disclosure (summary → detail → deep)
- [ ] Andragogy-compliant (immediate, relevant, practical)
- [ ] Minimal (doesn't re-document basics)

### Quality
- [ ] Active voice, present tense
- [ ] Clear, concise language
- [ ] Code examples tested
- [ ] Links work

### Accessibility
- [ ] Semantic structure
- [ ] Images have alt text
- [ ] Color contrast is good

### LLM Optimization (if applicable)
- [ ] Structured format
- [ ] Clear syntax
- [ ] Executive summary
- [ ] No ambiguity

---

## 🎯 Quick Examples

### Before (Current README - Bad)

```markdown
## Instalación y Configuración

### Requisitos Previos

- Python 3.14
- uv
- PostgreSQL
- Redis

### Instalación

```bash
git clone <repo-url>
cd backoffice_tramites
uv sync
```

### Base de Datos

**IMPORTANTE:** El esquema se gestiona externamente.

```bash
psql -U postgres -d sanfelipe_tramites -f sql/migrations/001_init_schema.sql
```

### Despliegue

```bash
docker-compose up -d
```

## Comandos de Desarrollo

```bash
uv run python manage.py runserver
uv run python manage.py shell
uv run python manage.py test
```
```

### After (Role-based - Good)

```markdown
# README.md

## 🚀 Quick Start

### Para Operadores
Empezar a usar el sistema: **[Tutorial: Crear tu primer trámite](docs/02-tutorials/operators/create-tramite.md)**

### Para Desarrolladores
Setup de desarrollo local: **[Tutorial: Setup de desarrollo](docs/02-tutorials/developers/local-dev-setup.md)**

### Para Sysadmins
Despliegue en producción: **[Guía: Despliegue en producción](docs/03-guides/sysadmins/deploy-production.md)**

---

## 📚 ¿Qué es este proyecto?

Sistema de gestión de trámites con gestión completa, catálogos configurables, sistema de costos y auditoría.

**Leer más**: [Overview completo](docs/01-onboarding/overview.md)

---

## 🔗 Enlaces útiles

- [Documentación completa](docs/README_MAP.md)
- [Arquitectura](docs/01-onboarding/architecture-overview.md)
- [API Reference](docs/05-reference/api/endpoints.md)
```

---

## 📖 Further Reading

### Methodologies
- [Diátaxis Framework](https://diataxis.fr/)
- [Progressive Disclosure in UX](https://www.nngroup.com/articles/progressive-disclosure/)
- [Information Architecture](https://www.nngroup.com/articles/ia-vs-navigation/)
- [Single Source of Truth](https://en.wikipedia.org/wiki/Single_source_of_truth)

### Technical Writing
- [Google Technical Writing One](https://developers.google.com/tech-writing/one)
- [Write the Docs](https://www.writethedocs.org/)
- [Microsoft Style Guide](https://docs.microsoft.com/en-us/style-guide/)

### LLM Optimization
- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)

---

## 🤝 Team Guidelines

### When Creating Documentation

1. **Start with the user**: Who is this for? What do they need?
2. **Choose the right category**: Tutorial, Guide, Concept, or Reference?
3. **Use the template**: Follow established templates
4. **Check for duplicates**: Does this already exist?
5. **Test it**: Can you follow your own instructions?
6. **Get feedback**: Ask someone from the target audience

### When Reviewing Documentation

1. **Check the audience**: Is it appropriate for the target role?
2. **Verify SSOT**: Is there duplication?
3. **Test links**: Do all links work?
4. **Review clarity**: Is it clear and concise?
5. **Validate examples**: Do code examples work?

### When Maintaining Documentation

1. **Update regularly**: Keep docs in sync with code
2. **Audit periodically**: Check for broken links and outdated info
3. **Collect feedback**: What are users struggling to find?
4. **Iterate**: Continuously improve based on feedback

---

*This quick reference is a living document. Update as needed.*

---

**Related Documents**:
- [Full Restructuring Plan](../RESTRUCTURING_PLAN.md)
- [Executive Summary](./EXECUTIVE_SUMMARY.md)
- [Documentation Map](./README_MAP.md)
- [Visual Diagram](./VISUAL_DIAGRAM.md)
