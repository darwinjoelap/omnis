# 00 — Índice del roadmap

Cada fase = una sesión (o pocas) con **criterio de salida verificable**.
El `.md` ejecutable de una fase se redacta **al iniciarla** con `_PLANTILLA_FASE.md`
(solo la 01 viene completa: la documentación escrita por adelantado envejece).

| # | Fase | Modelo sugerido | Depende de | Se apoya en | Criterio de salida |
|---|---|---|---|---|---|
| 00 | Diseño y documentación | Opus | — | este paquete | Darwin aprueba los ADR *Propuesta* |
| 01 | Esqueleto y despliegue a staging | Sonnet | 00 | Ordo | `/salud/` responde en staging; tests y `check --deploy` en verde |
| 02 | Tenancy, usuarios, equipo, permisos, plataforma, planes, auditoría | Sonnet | 01 | Ordo + Pediae (`Plan`, `Suscripcion`) | Dos tenants aislados (test), login por enlace, roles, suspensión y vencimiento funcionan |
| 03 | Configuración del tenant, lugares, especialidades y perfil profesional (firma/sello) | Sonnet | 02 | Pediae `configuracion`/`accounts`, Ordo `PerfilEmpresa` | Un médico con especialidad, firma y sello; branding aplicado; sin `/admin` |
| 04 | Tasa BCV y catálogo de servicios | Haiku | 02 | Ordo `tasas` | Cron registra la tasa; tasa del tenant; servicios con precio USD/Bs; indicador en barra |
| 05 | Pacientes y representantes | Sonnet | 03 | Pediae `pacientes` | Duplicados por documento avisados; menor sin documento exige representante; hermanos sí se registran; búsqueda rápida |
| 06 | ★ Motor de secciones y plantillas de historia | **Opus** | 05 | diseño propio | Esquema validado; form generado; plantilla armada por el médico; sección personalizada creada desde la app |
| 07 | ★ Consulta clínica (núcleo) | **Opus** | 06 | Pediae/Ginea `consultas` | Consulta con signos vitales, CIE-10, récipe, órdenes, adjuntos; cierre y enmienda; visibilidad según ADR-008 |
| 08 | Agenda multi-profesional | Sonnet | 07 | Pediae `agenda` | Horarios, bloqueos, tipos de cita, sin solapamientos; vista médico y clínica; "Atender" abre la consulta; WhatsApp |
| 09 | Cobros | Sonnet | 04, 08 | Pediae `ConsultaServicio` | Cargos con tasa congelada, pagos mixtos USD/Bs y abonos; cuentas por cobrar |
| 10 | Documentos PDF | Sonnet | 07 | Pediae/Ginea PDFs, Ordo `core/pdf.py` | Récipe, informe, referencia, reposo, constancia con firma/sello; abren en móvil |
| 11 | Reportes | Sonnet | 09, 10 | Pediae/Ginea `reportes` | Consultas, morbilidad CIE-10, agenda, ingresos USD/Bs por médico/especialidad; Excel y PDF |
| 12 | PWA instalable y offline de consulta | **Opus** | 10 | Ordo `pwa.py` + Pediae `offline/` | Instalada en iPhone y Android; consulta sin red sin perder datos; sin duplicados |
| 13 | Módulo Pediatría | Sonnet | 12 | Pediae | Paridad funcional con Pediae (percentiles, vacunas, pesquisas, dosis, constancias) |
| 14 | Módulo Ginecología y Obstetricia | Sonnet | 12 | Ginea | Paridad funcional con Ginea (antecedentes GO, control prenatal, FPP) |
| 15 | Producción: CI, respaldos, primer tenant real | Sonnet | 13 **o** 14 | Ordo `DESPLIEGUE_RAILWAY.md` | Producción operando con un médico real; respaldo verificado (restaurado en prueba) |
| 16 | Módulo Cardiología | Sonnet (+Opus para riesgo CV) | 15 | doctora cardióloga | Plantillas validadas por la doctora; ECG, riesgo CV, informe |
| 17 | Dictado por voz | **Opus** | 16 | — | Grabación en iPhone/Android → propuesta estructurada → revisión → guardado; uso medido por tenant |
| 18 | Migración de tenants de Ginea y Pediae (opcional) | Opus | 13, 14 | Ordo `migracion_biolife.py` | Simulación + verificación + importación en una transacción |
| 19 | Endurecimiento: 2FA, límites de intentos, pruebas de carga | Sonnet | 15 | — | 2FA para titulares; rate limiting; aislamiento verificado bajo carga |

## Ruta crítica al primer médico en producción

```
01 → 02 → 03 → 05 → 06 → 07 → 08 → 04 → 09 → 10 → 12 → (13 ó 14) → 15
```

La 11 (reportes) puede ir antes o después de la 15 según lo que pida el primer médico.
**No construir el panel de plataforma "bonito" ni más especialidades antes de tener el primer
médico usando el sistema** (lección de Biolife).

## Dependencias (lo mismo que la columna "Depende de", en cadena)

```
01 → 02 → 03 → 05 → 06 → 07 → 08 ┐
     02 → 04 ────────────────────┴→ 09 ┐
                    07 → 10 ───────────┴→ 11
                         10 → 12 → 13 ┐
                              12 → 14 ┴→ 15 → 16 → 17
                                  13 + 14 → 18        15 → 19
```
