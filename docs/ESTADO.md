# ESTADO — Omnis

> Se actualiza al **cerrar cada sesión** y es lo primero que se lee al abrir la siguiente.
> Menos de 100 líneas: el detalle de fases cerradas va a `HISTORIAL.md`; las decisiones, a `DECISIONES.md`.

**Última actualización:** 2026-10-20
**Fase actual:** 11 cerrada en código → siguiente **12 PWA offline** (ruta crítica) o 13/14 módulo de especialidad
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
- [x] Perfil del médico estilo Pediae: logo/marca de agua, banner, firma y sello fijos al pie (ADR-030)
- [x] Alcance de pacientes por rol (ADR-029): médico ve los suyos; asistente/titular ven todo; configurable
- [x] Marca **Omnis** (ADR-028): logo, paleta, fuentes locales, login en dos paneles, inicio con cifras del día

**Verificación:** 107 tests en verde en SQLite y PostgreSQL 16 · `ruff` limpio · `makemigrations --check` limpio ·
prueba E2E con navegador (escritorio y móvil) de paciente → consulta → cierre → PDF.

## Pendiente inmediato
1. Darwin: Python 3.14.3 confirmado — crear venv con Python 3.14 (`py -3.14 --version`), `pip install -r requirements-dev.txt`, `migrate`, `test`.
2. Darwin: prueba manual con `crear_tenant` (ver README) — revisar textos de reposo/constancia y el récipe impreso.
3. Crear proyecto Railway (Postgres, servicio web, servicio cron) → staging.
4. Fase 12 PWA offline · Fase 13/14 módulo Pediatría o Ginecología.

## Incompleto / provisional (decir siempre)
- ADR 002–007 y 009–019 aplicadas como provisionales (ADR-020): revisar.
- Logo: recortado del PNG entregado (no hay SVG): conviene el archivo vectorial para íconos nítidos.
- PDFs (ReportLab) siguen en Helvetica; solo cambian colores y nombre.
- CIE-10: solo 136 códigos frecuentes; falta CSV oficial → `importar_cie10`.
- Adjuntos: servidos por vista con login, pero aún no como `authenticated` en Cloudinary (ADR-017).
- Cierre automático de consultas: solo cuando corre el cron diario.
- Récipe muy largo: si no cabe en una hoja, se parte en columnas (sin repetir encabezado).
- Offline de consulta (Fase 12) no portado todavía: hoy la PWA instala y muestra página offline.
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
