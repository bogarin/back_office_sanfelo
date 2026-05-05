# AUDIT-{NNN}: {título corto del objetivo y alcance en kebab-case}

> **Fecha:** {YYYY-MM-DD}
> **Tipo:** {Calidad | Seguridad | Rendimiento | Documentación | Arquitectura}
> **Estado:** {En Progreso | Completada}

---

## 1. Objetivo

{Describa en 2-3 oraciones qué se audita y por qué. Ejemplo: "Evaluar la calidad de las pruebas unitarias y de integración del módulo X para verificar que cumplen con los criterios mínimos de cobertura y efectividad."}

## 2. Alcance

**Incluye:**
- {Módulo, archivo o componente específico}
- {Módulo, archivo o componente específico}

**Excluye:**
- {Lo que deliberadamente no se revisa y por qué}

## 3. Metodología y Criterios de Evaluación

{Describa el estándar o heurística utilizada como base. Sea específico y medible.}

| Criterio | Umbral aceptable | Referencia |
|----------|-----------------|------------|
| {Ej: Cobertura de líneas} | {Ej: ≥ 80%} | {Ej: estándar interno} |
| {Ej: Sin pruebas duplicadas} | {Ej: 0 duplicados} | {Ej: DRY} |

## 4. Hallazgos

### Críticos

> {Los que bloquean deploy o comprometen la integridad del sistema.}

- **H-{NNN}-001:** {Descripción del hallazgo}
  - **Severidad:** Crítico
  - **Evidencia:** {Archivo(s), línea(s), o dato cuantitativo}

### Altos

> {Los que degradan significativamente la calidad o mantenibilidad.}

- **H-{NNN}-002:** {Descripción del hallazgo}

### Medios

> {Los que deberían corregerse en el corto plazo.}

- **H-{NNN}-003:** {Descripción del hallazgo}

### Bajos

> {Mejoras deseables pero no urgentes.}

- **H-{NNN}-004:** {Descripción del hallazgo}

## 5. Acciones Correctivas

| Hallazgo | Acción | Responsable | Estado | Fecha límite |
|----------|--------|-------------|--------|--------------|
| H-{NNN}-001 | {Descripción de la corrección} | {Quién} | {Pendiente \| En Progreso \| Resuelto} | {YYYY-MM-DD} |

## 6. Métricas

{Datos cuantitativos que reflejen el estado antes y después de las correcciones. Si la auditoría aún no tiene post-corrección, registre solo el baseline.}

| Métrica | Baseline | Post-corrección | Delta |
|---------|----------|----------------|-------|
| {Ej: Cobertura global} | {Ej: 23%} | {Ej: 65%} | {Ej: +42 pp} |

## 7. Decisiones Derivadas

{Si la auditoría generó nuevos ADRs o cambios de arquitectura, lístelos aquí. Si no hubo, indique "Ninguna".}

- [{ADR-NNN}](../06-decisions/NNN-titulo.md): {Descripción breve de la decisión}

## 8. Documentos Relacionados

- [{Nombre del documento}](ruta/relativa.md) — {Relación: afectado, referenciado, actualizado}
