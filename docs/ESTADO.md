# ESTADO — Omnis

> Se actualiza al **cerrar cada sesión** y es lo primero que se lee al abrir la siguiente.
> Menos de 100 líneas: el detalle de fases cerradas va a `HISTORIAL.md`; las decisiones, a `DECISIONES.md`.

**Última actualización:** 2026-10-20
**Fase actual:** 12 cerrada en código → siguiente **13/14 módulo de especialidad** (Pediatría o Ginecología) o Railway staging
**Repositorio:** `github.com/darwinjoelap/omnis` (privado), rama `main` — código en `C:\proyectos\omnis`
**Staging / producción:** pendientes (Railway no creado)

---

## Completado (código + tests; falta prueba manual de Darwin)
- [x] 01 Esqueleto (settings por entorno, Dockerfile, railway.json, cron, `/salud/`)
- [x] 02 Tenancy, usuarios, equipo, permisos, plataforma, planes, auditoría
- [x] 03 Configuración del tenant, lugares, perfil profesional (firma, sello, membrete)
- [x] 04 Tasa BCV + tasa del tenant; servicios con precio USD
- [x] 05 Pacientes y representantes (duplicados, hermanos, menores)
- [x] 06 Motor de secciones y plantillas (el médico arma su historia)
- [x] 07 Consulta clínica: borrador/cierre/enmienda/anulación, CIE-10, adjuntos, cierre automático
- [x] 08 Agenda multi-profesional (horarios, bloqueos, tipos, sobrecupo, WhatsApp, «Atender»)
- [x] 09 Cobros: cargos, pagos USD/Bs, abonos, saldo a favor, caja del día, por cobrar
- [x] 10 Documentos PDF: récipe (2 columnas), informe, referencia, reposo, constancia, recibo
- [x] 11 Reportes: tablero con filtros, morbilidad CIE-10, agenda, ingresos, por profesional; PDF y Excel (ADR-031)
- [x] 12 PWA offline de consulta: borradores, cola con idempotencia, precarga y copias de agenda/fichas, consulta nueva sin red (ADR-032)
- [x] Perfil del médico estilo Pediae: logo/marca de agua, banner, firma y sello fijos al pie (ADR-030)
- [x] Alcance de pacientes por rol (ADR-029): médico ve los suyos; asistente/titular ven todo; configurable
- [x] Marca **Omnis** (ADR-028): logo, paleta, fuentes locales, login en dos paneles, inicio con cifras del día

**Verificación:** 118 tests en verde en SQLite y PostgreSQL 16 · `ruff` limpio · `makemigrations --check` limpio ·
E2E con navegador: paciente → consulta → cierre → PDF; offline (servidor apagado): copia de agenda, consulta nueva en cola, sincroniza al volver.

## Pendiente inmediato
1. Darwin: Python 3.14.3 confirmado — crear venv con Python 3.14 (`py -3.14 --version`), `pip install -r requirements-dev.txt`, `migrate`, `test`.
2. Darwin: prueba manual con `crear_tenant` (ver README) — revisar textos de reposo/constancia y el récipe impreso.
3. Crear proyecto Railway (Postgres, servicio web, servicio cron) → staging.
4. Darwin: probar offline en el teléfono (abrir la agenda con señal, modo avión, atender, volver a la señal).
5. Fase 13/14 módulo Pediatría o Ginecología.

## Incompleto / provisional (decir siempre)
- ADR 002–007 y 009–019 aplicadas como provisionales (ADR-020): revisar.
- Logo: recortado del PNG entregado (no hay SVG): conviene el archivo vectorial para íconos nítidos.
- PDFs (ReportLab) siguen en Helvetica; solo cambian colores y nombre.
- CIE-10: solo 136 códigos frecuentes; falta CSV oficial → `importar_cie10`.
- Adjuntos: servidos por vista con login, pero aún no como `authenticated` en Cloudinary (ADR-017).
- Cierre automático de consultas: solo cuando corre el cron diario.
- Récipe muy largo: si no cabe en una hoja, se parte en columnas (sin repetir encabezado).
- Offline: cada dispositivo debe abrir Omnis con señal al menos una vez (y la sesión debe seguir abierta); sin red no se crean pacientes nuevos, ni cobros, documentos/PDF o adjuntos; las filas dinámicas (diagnósticos, récipe) de un borrador se recuperan solo si ya existían en la página.
- Sin módulos de especialidad reales (Pediatría/Ginecología): solo Medicina General + básicas.

## Preguntas abiertas
- [ ] ¿Qué especialidad lleva el primer médico real a producción (13 ó 14)?
- [ ] ¿Migrar tenants de Ginea/Pediae (Fase 18)?
- [ ] Precio y planes (¿por profesional? ¿dictado como complemento?)
- [ ] Fuente oficial del CIE-10 en español
- [ ] Dominio: por definir (el correo de envío `no-responder@omnis.app` es provisional)

## Bloqueos
Ninguno.

## Notas
- Proyectos de referencia en `C:\proyectos\{ordo,pediae,ginea-saas,biolife}` — **no se tocan** desde aquí.
- Tests en Postgres: `DATABASE_URL=postgres://… python manage.py test`.
