# Fase NN — Nombre

> Estructura obligatoria de todo archivo de fase. Se redacta al **iniciar** la fase.
> Si al ejecutarla el modelo tiene que tomar decisiones de arquitectura, este archivo está incompleto:
> se corrige el `.md`, no se improvisa en el chat.

**Modelo sugerido:** Sonnet / Opus / Haiku
**Depende de:** Fase XX (cerrada)
**ADR relacionados:** ADR-0XX
**Se apoya en:** rutas exactas de los proyectos de referencia (ver `04_REUTILIZACION.md`)

## Objetivo
Una o dos frases. Qué podrá hacer el usuario al terminar.

## Fuera de alcance
Lo que **no** se hace en esta fase (y en cuál se hace).

## Decisiones previas a ejecutar
Opciones con pros/contras si hay más de un camino. Darwin elige antes de escribir código.

## Modelos
Modelo, campos, constraints, índices. Migración(es) esperada(s) con nombre.

## Services y selectors
Firma de cada función pública y reglas que aplica.

## Vistas, URLs y plantillas
Ruta, permiso requerido, qué muestra, comportamiento offline (`data-offline`, PDF con `data-pdf`).

## Tareas (checklist)
- [ ] 1. …
- [ ] 2. …

## Tests
- [ ] Reglas de negocio y casos borde
- [ ] Caso agregado a `tests/test_aislamiento.py` si hay modelos [T]

## Criterio de salida (verificable)
- [ ] …

## Verificación manual (Darwin)
Pasos concretos en el navegador / móvil.

## Cierre
- [ ] `docs/ESTADO.md` actualizado
- [ ] ADR nuevos en `docs/DECISIONES.md`
- [ ] Resumen en `docs/HISTORIAL.md`
- [ ] Commit(s): `feat(...)` en `develop`
- [ ] Lista explícita de lo que quedó **pendiente o incompleto**
