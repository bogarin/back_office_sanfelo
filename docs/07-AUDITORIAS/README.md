# Registro de Auditorías Técnicas

> "Si no documentas el estado real de tu sistema, estás navegando a ciegas. Una auditoría no es un castigo — es una radiografía que te dice exactamente dónde estás parado y qué necesitas arreglar antes de que sea una emergencia." — Pietro

## ¿Qué es una auditoría técnica y por qué nos importa?

Una **auditoría técnica** es una evaluación sistemática de un aspecto del sistema contra criterios objetivos y medibles. No es opinión — es evidencia.

**Beneficios para el Equipo:**
- **Visibilidad real:** Saber si las pruebas realmente protegen el código, si la seguridad tiene huecos, o si la documentación miente.
- **Toma de decisiones con datos:** En lugar de "creo que las pruebas están bien", tener métricas concretas (cobertura 23%, 15 hallazgos críticos).
- **Prevención:** Detectar problemas antes de que lleguen a producción.

**Beneficios para Agentes LLM:**
- **Contexto de calidad:** Cuando un agente deba escribir código, tests o documentación, las auditorías le indican qué estándares se exigen y qué errores ya se detectaron.
- **Criterios verificables:** Los criterios de evaluación de cada auditoría son reglas que un agente puede verificar automáticamente.

## Índice de Auditorías

> Los más recientes aparecen primero.

| Fecha | Archivo | Tipo | Descripción |
| ----- | ------- | ---- | ----------- |
| 2026-05-04 | [AUDIT-002](002-limpieza-de-codigo.md) | Calidad | Limpieza de código: 50 hallazgos, 4 críticos, 8 altos, antipatrones de mantenibilidad |
| 2026-05-04 | [AUDIT-001](001-calidad-de-pruebas.md) | Calidad | Calidad de pruebas unitarias/integración: 12 hallazgos, 344 tests, 100% pass rate |

## Cómo crear una nueva auditoría

El proceso es simple, no hay excusas:

1. **Copiar** el archivo [`audit-template.md`](audit-template.md) a un nuevo archivo con el formato `NNN-descripcion-y-alcance.md` dentro de este directorio (`docs/07-AUDITORIAS`).
   - `NNN` es el número consecutivo (ej. 001, 002).
   - `descripcion-y-alcance` es una descripción corta en kebab-case del objetivo y alcance de la auditoría. Omitir la palabra "auditoria" en este nombre.
2. **Rellenar las 8 secciones** del template:
   - **Objetivo** — Qué se audita y por qué.
   - **Alcance** — Qué está dentro y fuera de la revisión.
   - **Metodología y Criterios** — Estándares medibles contra los que se evalúa.
   - **Hallazgos** — Lo encontrado, clasificado por severidad (Crítico, Alto, Medio, Bajo).
   - **Acciones Correctivas** — Qué se hace para resolver cada hallazgo, con estado y responsable.
   - **Métricas** — Datos cuantitativos antes/después (baseline y post-corrección).
   - **Decisiones Derivadas** — ADRs o cambios de arquitectura generados por esta auditoría.
   - **Documentos Relacionados** — ADRs, guías o referencia técnica afectada.
3. **Actualizar el índice** de este README. Los más recientes van primero.

### Convenciones

- **Numeración de hallazgos:** `H-{NNN}-{SEQ}` (ej. H-001-001, H-001-002).
- **Severidades:** Crítico → Alto → Medio → Bajo. No inventar niveles nuevos.
- **Métricas siempre:** Toda auditoría debe incluir al menos una métrica cuantitativa. Sin datos no hay auditoría.
- **Formato:** Markdown, enlaces relativos, en español.

---
*Mantengan este directorio limpio y ordenado. Una auditoría sin hallazgos documentados es una auditoría que nunca existió.*
