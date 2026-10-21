# 01 — Modelo de datos

> Nombres de modelos y campos **en español** (ADR-016), igual que Ginea, Pediae y Ordo, para
> poder portar código sin traducirlo. Este documento fija entidades, relaciones y reglas;
> el detalle de cada campo se cierra en la fase que crea el modelo.
>
> Convención: **[T]** = hereda `TenantModel` (FK `tenant` obligatorio, `objects` filtra).
> Todo modelo [T] además lleva `creado_en`, `actualizado_en`, `creado_por` (mixin `Auditable`).

## 1. Plataforma (sin tenant)

| Modelo | Campos clave | Notas |
|---|---|---|
| `Tenant` | nombre, slug (único), estado (activo/suspendido), plan FK, activo_hasta, limite_profesionales, limite_usuarios, notas | Origen: `Empresa` de Ordo + `Tenant` de Pediae |
| `Plan` | nombre, tipo (mensual/anual), precio_usd, max_profesionales, max_usuarios, incluye_dictado, minutos_dictado_mes, activo | Origen: `Plan` de Pediae |
| `Suscripcion` | tenant, plan, estado (trial/activa/vencida/suspendida), fecha_inicio, fecha_fin, notas | Activación manual por Darwin (como hoy) |
| `Especialidad` | codigo (único: `pediatria`, `ginecologia`…), nombre, modulo (ruta de la app), activa, color, icono | Catálogo global; las filas las crea `sincronizar_especialidades` |
| `TenantEspecialidad` | tenant, especialidad | Qué especialidades tiene habilitadas cada tenant (por plan) |
| `TasaCambio` | fecha (única), bs_por_usd (14,4), fuente (BCV/MANUAL), registrada_por | Copia de Ordo |
| `Cie10` | codigo (único), descripcion, capitulo, es_categoria | Catálogo maestro en español; carga por fixture (Fase 07) |

## 2. Usuarios y equipo

| Modelo | Campos clave | Notas |
|---|---|---|
| `Usuario` (AbstractUser) | username, tenant_cuenta (null = cuenta de plataforma), debe_cambiar_clave, telefono, sexo | Usuario único **por tenant** (constraint `tenant_cuenta + username`), como Ordo |
| `Membresia` | usuario, tenant, rol, activa | Rol: `TITULAR`, `ADMIN`, `MEDICO`, `ASISTENTE`. Un usuario puede tener membresías en varios tenants |
| `PerfilProfesional` [T] | membresia (1-1), especialidad FK, subespecialidad (texto), titulo_mostrar (Dr./Dra.), credenciales, numero_mpps, numero_colegio, firma (Cloudinary), sello (Cloudinary), membrete propio (opcional), usar_membrete_propio | **Una especialidad por médico dentro del tenant** (requisito). El mismo médico en otro tenant puede tener otra |

> Regla: `MEDICO` exige `PerfilProfesional` con especialidad habilitada en el tenant.

## 3. Configuración del tenant

| Modelo | Campos clave |
|---|---|
| `ConfiguracionTenant` [T] (1-1) | nombre_mostrar, logo, color_primario, color_lateral, direccion, telefono, email, whatsapp, mensaje_whatsapp, membrete (imagen), pie_documentos, **visibilidad_historia** (COMPARTIDA / POR_ESPECIALIDAD / PRIVADA), **medicos_ven_todos_pacientes** (ADR-029), horas_edicion_consulta (para el cierre automático), dictado_activo, formato_cedula |
| `Lugar` [T] | nombre, ciudad, direccion, telefono, activo, orden |
| `TasaTenant` [T] | fecha, bs_por_usd, registrada_por — único (tenant, fecha) |

## 4. Pacientes

| Modelo | Campos clave | Reglas |
|---|---|---|
| `Paciente` [T] | nombres, apellidos, sexo, fecha_nacimiento (o edad declarada), tipo_documento (V/E/P/sin documento), numero_documento, telefono, email, direccion, ocupacion, estado_civil, grupo_sanguineo, seguro, contacto_emergencia, foto (opcional), activo, origen (cómo llegó) | Documento único por tenant (`iexact`, normalizado). Duplicado → aviso + "Abrir su ficha" (lógica de Pediae) |
| `Representante` [T] | paciente FK, nombre, parentesco, tipo/número de documento, telefono, ocupacion, es_principal | **Menor sin documento exige representante principal.** El documento del representante **no** es único (hermanos — pendiente que hoy bloquea a Pediae) |
| `AntecedenteBase` [T] (1-1 paciente) | alergias, medicacion_actual, enfermedades_cronicas, cirugias_previas, hospitalizaciones, habitos (tabaco, alcohol, otros), antecedentes_familiares (lista estructurada) | Lo común a toda especialidad. Siempre visible para todo médico del tenant |

Los antecedentes **propios de una especialidad** (perinatales, gineco-obstétricos, cardiovasculares)
**no** van en `Paciente`: son `RegistroSeccionPaciente` (ámbito PACIENTE, §6).

## 5. Agenda

| Modelo | Campos clave |
|---|---|
| `HorarioAtencion` [T] | profesional (PerfilProfesional), lugar, dia_semana, hora_inicio, hora_fin, duracion_turno_min, vigente_desde, vigente_hasta |
| `Bloqueo` [T] | profesional (o null = toda la clínica), desde, hasta, motivo |
| `TipoCita` [T] | nombre, especialidad (opcional), duracion_min, color, servicio_por_defecto, plantilla_por_defecto, activo |
| `Cita` [T] | paciente, profesional, especialidad (congelada), lugar, tipo, fecha, hora_inicio (opcional), hora_fin (opcional), estado, motivo, notas, recordatorio_enviado_en, recordatorio_canal, cancelada_motivo |

Estados de `Cita`: `TENTATIVA → PROGRAMADA → CONFIRMADA → EN_SALA → ATENDIDA`; laterales
`CANCELADA`, `NO_ASISTIO`. Transiciones solo en `agenda/services.py`.

## 6. ★ Clínica (motor de historia)

### 6.1 Catálogo de secciones

```
SeccionClinica
  tenant          FK null      → null = del sistema (núcleo o módulo); con valor = personalizada del tenant
  codigo          slug         → único por (tenant, codigo); módulos usan prefijo: "ped.antropometria"
  nombre
  tipo            NUCLEO | MODULO | PERSONALIZADA
  ambito          CONSULTA | PACIENTE
  especialidad    FK null      → null = general
  version         int          → sube cuando cambia el esquema
  esquema         JSONB        → ver 6.2 (en NUCLEO puede venir vacío: tiene tablas propias)
  activa          bool
  creada_por      FK null
```

`SeccionClinicaVersion` guarda cada esquema anterior (sección, version, esquema) para poder
leer e imprimir registros viejos.

### 6.2 Formato del esquema (contrato único)

```json
{
  "campos": [
    {"clave": "peso", "tipo": "numero", "etiqueta": "Peso", "unidad": "kg",
     "min": 0.3, "max": 300, "decimales": 2, "requerido": true},
    {"clave": "talla", "tipo": "numero", "etiqueta": "Talla", "unidad": "cm", "decimales": 1},
    {"clave": "imc", "tipo": "calculado", "etiqueta": "IMC", "funcion": "general.imc",
     "depende_de": ["peso", "talla"]},
    {"clave": "dolor_toracico", "tipo": "si_no", "etiqueta": "Dolor torácico"},
    {"clave": "caracteristicas_dolor", "tipo": "texto_largo", "etiqueta": "Características",
     "visible_si": {"campo": "dolor_toracico", "igual": true}},
    {"clave": "nyha", "tipo": "opcion", "etiqueta": "Clase funcional NYHA",
     "opciones": [["I","I"],["II","II"],["III","III"],["IV","IV"]]}
  ],
  "diseno": {"columnas": 12, "filas": [["peso:3","talla:3","imc:3"], ["dolor_toracico:3","caracteristicas_dolor:9"]]}
}
```

Tipos: `texto`, `texto_largo`, `numero`, `fecha`, `hora`, `si_no`, `opcion`, `opciones`
(múltiple), `checklist`, `escala` (min/max/paso), `tabla` (subcampos, filas repetibles),
`calculado` (solo `tipo=MODULO`; `funcion` apunta a una función registrada en Python).
Validación: `clinica/esquemas.py` (un solo validador para formulario, API offline y dictado).

### 6.3 Plantillas

```
PlantillaHistoria [T]
  profesional     FK null      → null = plantilla de la clínica
  especialidad    FK
  nombre                       → "Primera consulta", "Control", "Control prenatal"
  es_predeterminada bool
  activa

PlantillaSeccion [T]
  plantilla, seccion, orden, obligatoria, colapsada
  ajustes JSONB  → {"ocultos": ["caracteristicas_dolor"], "etiquetas": {"nyha": "NYHA"}}
```

Cada módulo trae **plantillas iniciales** que se copian al tenant al habilitar la especialidad
(el médico parte de algo útil y lo ajusta).

### 6.4 Consulta y registros

| Modelo | Campos clave | Reglas |
|---|---|---|
| `Consulta` [T] | paciente, profesional, especialidad (congelada), cita (1-1, opcional), lugar, plantilla, **estructura** (JSONB: copia congelada de la plantilla con versiones de sección), fecha_hora, tipo (primera vez/control/emergencia/…), estado (BORRADOR/CERRADA/ANULADA), cerrada_en, motivo_consulta, enfermedad_actual, plan, indicaciones_generales, proxima_cita_sugerida | Cerrada = inmutable. Cierre manual o automático tras `horas_edicion_consulta` (cron) |
| `RegistroSeccion` [T] | consulta, seccion, version_seccion, datos (JSONB), completada | Único (consulta, seccion). Índice GIN en `datos` |
| `RegistroSeccionPaciente` [T] | paciente, seccion, version_seccion, datos, vigente (bool), reemplaza FK | Ámbito PACIENTE: al editar se crea uno nuevo y el anterior queda `vigente=False` (historial) |
| `SignosVitales` [T] | consulta, peso_kg, talla_cm, imc, pa_sistolica, pa_diastolica, fc, fr, temperatura, spo2, glicemia_capilar, perimetro_abdominal | Tabla (no JSON) para graficar evolución |
| `DiagnosticoConsulta` [T] | consulta, cie10 FK null, texto, tipo (principal/secundario), certeza (presuntivo/definitivo), orden | CIE-10 opcional pero sugerido; favoritos por profesional |
| `DiagnosticoFavorito` [T] | profesional, cie10, texto, uso_contador | Autocompletar |
| `Medicamento` [T] | nombre, principio_activo, presentacion, concentracion, via, indicaciones_por_defecto, activo | Catálogo del tenant (glosario de Ginea/Pediae). Pediatría extiende con dosis por kg |
| `Prescripcion` [T] | consulta, observaciones | Una por consulta (récipe) |
| `ItemPrescripcion` [T] | prescripcion, medicamento FK null, texto, dosis, via, frecuencia, duracion, cantidad, indicaciones, orden | |
| `OrdenExamen` [T] | consulta, tipo (laboratorio/imagen/otro), items (texto o catálogo), indicaciones | |
| `Adjunto` [T] | paciente, consulta (opcional), archivo (Cloudinary **authenticated**), nombre, tipo, tamaño | Nunca URL pública |
| `Enmienda` [T] | consulta, autor, motivo, cambios (JSONB antes/después), creada_en | Única forma de corregir una consulta cerrada |

## 7. Cobros

| Modelo | Campos clave | Reglas |
|---|---|---|
| `Servicio` [T] | nombre, especialidad (opcional), precio_usd, costo_usd (opcional), activo | Único (tenant, nombre) |
| `Cargo` [T] | paciente, consulta o cita, servicio, profesional, precio_usd (congelado), descuento_usd, exonerado, tasa (congelada), estado (pendiente/pagado/anulado) | Se crea al atender o desde la cita |
| `Pago` [T] | paciente, fecha, monto, moneda (USD/Bs), metodo (efectivo, pago móvil, transferencia, Zelle, punto, otro), referencia, tasa, registrado_por | |
| `PagoAplicado` [T] | pago, cargo, monto_usd | Un pago puede cubrir varios cargos y abonos parciales |

## 8. Transversal

| Modelo | Campos clave |
|---|---|
| `Auditoria` [T] | usuario, accion (ver/crear/editar/cerrar/enmendar/imprimir/exportar), objeto (tipo + id), paciente FK null, ip, detalle, creado_en |
| `Secuencia` [T] | codigo, año, ultimo — correlativos (récipes, informes) sin carreras (de Ordo) |
| `SolicitudIdempotente` | clave, usuario, estado, respuesta — de `offline/` de Pediae |
| `UsoDictado` [T] (Fase 17) | consulta, profesional, segundos_audio, proveedor, tokens, costo_estimado |

## 9. Módulos de especialidad: dónde va cada cosa

| Necesidad | Dónde |
|---|---|
| Campos que se llenan en cada consulta | Sección `MODULO`, ámbito CONSULTA (JSONB) |
| Antecedentes propios de la especialidad | Sección `MODULO`, ámbito PACIENTE |
| Series que se grafican o cuentan (vacunas aplicadas, controles de presión domiciliaria) | **Modelo propio del módulo** [T] (p. ej. `pediatria.VacunaAplicada`) y una sección que lo edita |
| Cálculos (percentiles OMS, FPP, edad gestacional, riesgo CV, dosis por kg) | Funciones registradas del módulo (`calculos.py`) usadas por campos `calculado` |
| Documentos propios | `documentos.py` del módulo, registrados |
| Catálogos semilla (esquema de vacunas, pesquisas) | `fixtures/` del módulo + comando de siembra por tenant |

## 10. Restricciones de BD que deben existir

- `Paciente`: único (tenant, tipo_documento, numero_documento) cuando hay documento.
- `RegistroSeccion`: único (consulta, seccion).
- `Cita`: CHECK `hora_fin > hora_inicio` cuando ambas existen.
- `Cargo`: CHECK `precio_usd >= 0`, `descuento_usd <= precio_usd`.
- `TasaTenant`: único (tenant, fecha).
- `Membresia`: única (usuario, tenant).
- `PerfilProfesional.especialidad` ∈ especialidades habilitadas del tenant (validado en service).
