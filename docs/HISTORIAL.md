# HISTORIAL — Omnis

> Resumen de cada fase **cerrada** (lo que se hizo, commits, verificación, pendientes que pasaron
> a otra fase). Lo más reciente arriba. El detalle vivo está en `ESTADO.md` mientras la fase está abierta.

## Plantilla de entrada

```
### Fase NN — Nombre (AAAA-MM-DD)
- Hecho: …
- Verificado: N tests en verde (SQLite + PostgreSQL), ruff limpio, prueba manual de Darwin
- Commits: `abc1234`, `def5678`
- ADR: 0XX, 0YY
- Pasó a otra fase: … (Fase MM)
```

---

### Fase 11 + perfil Pediae (2026-10-20)
- Hecho: app `reportes` (tablero, PDF, Excel), perfil profesional con logo/marca de agua/banner, firma y sello fijos al pie de los PDF, documento de muestra por médico.
- Verificado: 107 tests (SQLite + PostgreSQL), ruff limpio, capturas escritorio/móvil y PDF revisados.
- ADR: 030, 031.

### Fases 01–10 — Base, clínica, agenda, cobros y documentos (2026-10-20)
- Hecho: esqueleto y despliegue preparado (sin crear Railway); tenancy fail-closed con `TenantModel`;
  login por enlace del consultorio; roles + pseudo-rol PROFESIONAL; plataforma (planes, suscripciones,
  soporte sin acceso a historias); configuración, lugares y perfil profesional; tasa BCV (de Ordo);
  pacientes/representantes; motor de secciones (esquema JSON versionado, plantillas del médico, secciones
  personalizadas); consulta (borrador, cierre, enmienda, anulación, CIE-10, signos, prescripción, adjuntos,
  cierre automático); agenda multi-profesional; cobros con abonos y saldo a favor; documentos PDF con
  número correlativo (récipe dos columnas de Ginea, informe, referencia, reposo, constancia, recibo).
- Verificado: 96 tests (SQLite + PostgreSQL 16), ruff limpio, E2E Playwright escritorio/móvil.
- Commits: sin repositorio todavía (archivos en `C:\proyectos\omnis`).
- ADR: 020–027 (provisionales).
- Pasó a otra fase: offline de consulta (12), adjuntos `authenticated` (15), CIE-10 completo (pendiente de archivo).

### Fase 00 — Diseño (2026-10-19, abierta hasta aprobar ADR)
- Revisión de Ginea, Pediae, Ordo y Biolife; paquete de documentación inicial.
