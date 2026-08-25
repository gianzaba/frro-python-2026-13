# 📘 DOCUMENTACIÓN COMPLETA DEL SISTEMA: INMOGESTIÓN B2B
**Sistema de Gestión Integral y Backoffice Operativo para Inmobiliarias**
*Versión: 2.0 (Edición Completa - 2026)*

---

## 📑 ÍNDICE GENERAL
1. [Visión General y Arquitectura del Sistema](#1-visión-general-y-arquitectura-del-sistema)
2. [Estructura de la Arquitectura en 3 Capas](#2-estructura-de-la-arquitectura-en-3-capas)
3. [Modelo de Dominio y Entidades del Sistema](#3-modelo-de-dominio-y-entidades-del-sistema)
4. [Módulos y Funcionalidades Detalladas](#4-módulos-y-funcionalidades-detalladas)
   - 4.1. [Autenticación, Seguridad y Gestión de Roles](#41-autenticación-seguridad-y-gestión-de-roles)
   - 4.2. [Dashboard Ejecutivo y Métricas Globales](#42-dashboard-ejecutivo-y-métricas-globales)
   - 4.3. [Gestión de Clientes e Inquilinos](#43-gestión-de-clientes-e-inquilinos)
   - 4.4. [Gestión de Propietarios](#44-gestión-de-propietarios)
   - 4.5. [Catálogo de Propiedades y Comercialización](#45-catálogo-de-propiedades-y-comercialización)
   - 4.6. [Análisis Estratégico de Inactividad y Vacancia de Propiedades](#46-análisis-estratégico-de-inactividad-y-vacancia-de-propiedades)
   - 4.7. [Agenda de Visitas con Control Estricto de Cupos](#47-agenda-de-visitas-con-control-estricto-de-cupos)
   - 4.8. [Contratos Legales, Cláusulas Dinámicas e Inmutabilidad](#48-contratos-legales-cláusulas-dinámicas-e-inmutabilidad)
   - 4.9. [Reclamos, Roturas Estructurales y Presupuestos para Propietarios](#49-reclamos-roturas-estructurales-y-presupuestos-para-propietarios)
   - 4.10. [Finanzas, Cobro de Alquileres, Mora y Boletas en PDF](#410-finanzas-cobro-de-alquileres-mora-y-boletas-en-pdf)
   - 4.11. [Liquidaciones a Propietarios y Exportaciones](#411-liquidaciones-a-propietarios-y-exportaciones)
   - 4.12. [Gestión y Alta de Agentes Comerciales (Exclusivo Administrador)](#412-gestión-y-alta-de-agentes-comerciales-exclusivo-administrador)
5. [Matriz de Reglas de Negocio y Restricciones Operativas](#5-matriz-de-reglas-de-negocio-y-restricciones-operativas)
6. [Catálogo Completo de Endpoints y Rutas HTTP](#6-catálogo-completo-de-endpoints-y-rutas-http)
7. [Fórmulas y Cálculos Financieros del Sistema](#7-fórmulas-y-cálculos-financieros-del-sistema)
8. [Datos de Prueba y Credenciales de Acceso](#8-datos-de-prueba-y-credenciales-de-acceso)

---

## 1. VISIÓN GENERAL Y ARQUITECTURA DEL SISTEMA

**InmoGestión B2B** es una plataforma web integral diseñada para la administración operativa, legal y financiera de una agencia inmobiliaria moderna. Permite digitalizar todo el ciclo de vida del negocio inmobiliario: desde la captación del inmueble y asignación comercial a los agentes, coordinación de agendas de visitas con cupos limitados, generación y firma de contratos legales con cláusulas inmutables, gestión de reclamos de roturas estructurales con cotizaciones para los dueños, hasta el cobro de cánones locativos con cálculo automático de mora diaria, emisión de boletas imprimibles y liquidaciones netas a propietarios.

### Stack Tecnológico
- **Lenguaje Principal:** Python 3.10+ (100% compliant con PEP 8).
- **Framework Web:** Flask (Arquitectura modular basada en Blueprints y Context Processors).
- **Capa de Persistencia:** SQLAlchemy ORM con compatibilidad dual para SQLite local y PostgreSQL de producción.
- **Seguridad Criptográfica:** Werkzeug Security (`pbkdf2:sha256` para hashing irreversible de contraseñas).
- **Capa de Presentación:** Jinja2 Templates, HTML5 Semántico, CSS3 Personalizado con diseño B2B Glassmorphism / Dark Mode adaptativo (Mobile-First) y Bootstrap Icons.
- **Suite de Pruebas:** Pytest (25 pruebas unitarias y de integración con aislamiento en memoria).

---

## 2. ESTRUCTURA DE LA ARQUITECTURA EN 3 CAPAS

El sistema respeta estrictamente una separación en 3 capas desacopladas, donde el flujo de dependencias es estrictamente unidireccional: `Presentación -> Negocio -> Datos`.

```
┌────────────────────────────────────────────────────────┐
│               1. CAPA DE PRESENTACIÓN                  │
│       views/views.py  +  templates/  +  static/        │
│   (Controladores HTTP, Renderizado Jinja2, Sesiones)   │
└───────────────────────────┬────────────────────────────┘
                            │ (Solo invoca a la Capa de Negocio)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 2. CAPA DE NEGOCIO                     │
│    business/controller.py  +  business/entities.py     │
│   (Reglas de Negocio, Validaciones, Objetos Dominio)   │
└───────────────────────────┬────────────────────────────┘
                            │ (Solo invoca a la Capa de Datos)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  3. CAPA DE DATOS                      │
│                      datos/db.py                       │
│    (Modelos SQLAlchemy, CRUD, Consultas a DB, SQL)     │
└────────────────────────────────────────────────────────┘
```

- **Regla Estricta 1:** La Capa de Presentación tiene **prohibición absoluta** de importar o ejecutar métodos de `datos/db.py` o escribir consultas SQL.
- **Regla Estricta 2:** La Capa de Negocio no maneja respuestas HTTP, HTML ni sesiones; trabaja únicamente con objetos de dominio (`business/entities.py`).
- **Regla Estricta 3:** La Capa de Datos es la única autorizada a interactuar con las tablas físicas de la base de datos y siempre retorna entidades de dominio a la capa superior.

---

## 3. MODELO DE DOMINIO Y ENTIDADES DEL SISTEMA

### Jerarquía de Personas
- **`Persona` (Clase Base):** `id`, `tipo_doc`, `nro_doc`, `nombre`, `apellido`, `domicilio`, `telefono`, `email`, `contrasegna_hash`. Propiedad calculada: `nombre_completo`.
- **`Cliente` (Inquilino / Comprador):** Hereda de `Persona`. Representa a la contraparte que alquila o adquiere inmuebles.
- **`Propietario` (Locador / Vendedor):** Hereda de `Persona`. Representa al dueño del inmueble y titular de las liquidaciones de renta.
- **`Agente` (Martillero / Empleado):** Hereda de `Persona`. Agrega `cuil`, `matricula` profesional y `rol` (`"Administrador"` o `"Estándar"`).

### Entidades Operativas y Comerciales
- **`Propiedad`:** `id`, `direccion`, `tipo` (*Alquiler, Venta, etc.*), `zona`, `estado` (*disponible, alquilada, vendida*), `id_propietario`, `fecha_disponibilidad`.
- **`AgenteAsignado`:** `id_agente`, `id_propiedad`, `fecha_hora_desde`, `fecha_hora_hasta` (None si es activa). Vincula a un agente con la comercialización de un inmueble. Un agente puede tener asignadas múltiples propiedades en simultáneo.
- **`AgendaVisita`:** `id`, `id_propiedad`, `id_agente`, `fecha_hora_visita`, `duracion_minutos`, `cupo_maximo`, `estado` (*disponible, completo, cancelada*).
- **`InscripcionVisita`:** `id`, `id_agenda`, `id_cliente` (opcional), `nombre_visitante`, `telefono_visitante`, `email_visitante`, `observaciones`, `fecha_registro`, `asistio`.
- **`Contrato`:** `nro_contrato`, `fecha_solicitud`, `estado` (*solicitado, activo, finalizado, rescindido*), `fecha_contrato`, `id_cliente`, `id_agente`, `id_propiedad`, `monto`, `comision_porcentaje`, `comision_agente_porcentaje`, `tipo_contrato` (*Alquiler, Compraventa*), `ruta_documento_respaldo`.
  - Propiedades calculadas: `monto_honorarios_totales`, `monto_comision_agente`, `monto_comision_inmobiliaria`.
- **`Clausula`:** `id`, `nro_contrato`, `orden`, `titulo`, `contenido`. Texto legal de los contratos.
- **`Reclamo`:** `id`, `nro_contrato`, `id_propiedad`, `id_cliente`, `fecha_reclamo`, `tipo_dano`, `descripcion`, `urgencia` (*Baja, Media, Alta, Urgente*), `presupuesto_estimado`, `estado` (*pendiente, informado_propietario, en_reparacion, resuelto, desestimado*), `observaciones_resolucion`, `fecha_resolucion`.
- **`PagoInquilino`:** `id`, `nro_contrato`, `fecha_pago`, `monto`, `mes_correspondiente` (*formato YYYY-MM*), `fecha_vencimiento`, `dias_retraso`, `monto_recargo`, `monto_total_abonado`, `ruta_comprobante`.
- **`PagoPropietario` (Liquidación):** `id`, `id_propietario`, `nro_contrato`, `fecha_liquidacion`, `fecha_pago`, `mes_correspondiente`, `monto_bruto`, `comision`, `monto_neto`, `estado` (*pendiente, pagado*).

---

## 4. MÓDULOS Y FUNCIONALIDADES DETALLADAS

### 4.1. Autenticación, Seguridad y Gestión de Roles
- **Inicio de Sesión Seguro (`/login`):** Validación de credenciales contra contraseñas hasheadas (`pbkdf2:sha256`).
- **Control de Sesión:** Manejo de sesiones de usuario en cookies encriptadas (`agente_id`, `agente_name`, `agente_rol`).
- **Decoradores de Protección:**
  - `@login_required`: Restringe el acceso únicamente a agentes autenticados.
  - `@admin_required`: Restringe el acceso exclusivamente a agentes con rol `Administrador` (ej. liquidaciones masivas, pagos a propietarios, exportación CSV, gestión de agentes).
- **Cierre de Sesión (`/logout`):** Destrucción limpia y segura de la sesión activa.

### 4.2. Dashboard Ejecutivo y Métricas Globales
- **Ruta:** `/` o `/dashboard`.
- **Métricas en Tiempo Real (KPI Cards):**
  - Total de Propiedades disponibles, alquiladas y vendidas.
  - Cartera de Clientes e Inquilinos activos.
  - Total de Contratos vigentes y solicitudes en trámite.
  - Total cobrado en el mes en curso y pendiente de cobro.
- **Tablas de Actividad Reciente:** Accesos directos a contratos recién solicitados, turnos de visitas programados y accesos rápidos a módulos clave.

### 4.3. Gestión de Clientes e Inquilinos
- **Listado de Clientes (`/clientes`):** Vista de todos los clientes con datos de contacto, documento y dirección.
- **Alta de Nuevos Clientes (`/clientes/nuevo`):** Formulario con validación de documento (tipo + número) y email únicos.

### 4.4. Gestión de Propietarios
- **Listado de Propietarios (`/propietarios`):** Tabla con todos los locadores y vendedores registrados.
- **Alta de Propietarios (`/propietarios/nuevo`):** Registro de nuevos dueños con validación de documentos y datos de contacto.

### 4.5. Catálogo de Propiedades y Comercialización
- **Listado de Inmuebles (`/propiedades`):**
  - Catálogo con filtros por estado (*Disponible, Alquilada, Vendida*), tipo (*Casa, Depto, Local, Oficina, Terreno*) y zona.
  - Muestra el agente comercial actualmente asignado a cada propiedad.
- **Alta de Propiedad (`/propiedades/nueva`):** Asocia la propiedad al propietario correspondiente e inicializa su estado como `disponible` y fecha de disponibilidad.
- **Ficha de Detalle de Propiedad (`/propiedades/<id>`):**
  - Ficha técnica completa del inmueble.
  - Historial de contratos celebrados.
  - Historial de comercialización y asignaciones de agentes.
- **Asignación de Agente Comercial (`/propiedades/<id>/asignar`):**
  - Permite asignar a un agente comercial para la gestión y comercialización del inmueble.
  - Finaliza de forma automática la asignación activa previa de esa propiedad.
  - **Flexibilidad:** Un mismo agente puede tener asignadas múltiples propiedades simultáneamente.

### 4.6. Análisis Estratégico de Inactividad y Vacancia de Propiedades
- **Ruta:** `/propiedades/inactivas`.
- **Objetivo:** Identificar inmuebles que llevan un tiempo prolongado sin alquilarse ni venderse para permitir al martillero tomar decisiones informadas y negociar bajas de precio o cambios de estrategia con los propietarios.
- **Cálculo de Días Vacantes:** $\text{Días de Oferta} = \text{Fecha Actual} - \text{Fecha de Disponibilidad}$.
- **Matriz de Diagnóstico y Plan de Acción Automático:**
  1. **Nivel Bajo ($\le 30$ días vacante):** Badge Verde. Diagnóstico: *"Período de comercialización saludable y dentro del promedio del mercado."* Plan: *"Mantener precio y monitorear consultas."*
  2. **Nivel Moderado ($31 - 60$ días vacante):** Badge Amarillo. Diagnóstico: *"Tiempo en oferta superior al promedio. Interés moderado."* Plan: *"Reforzar difusión en portales destacados y evaluar ajuste de precio sugerido (-5%)."*
  3. **Nivel Alto ($61 - 90$ días vacante):** Badge Naranja. Diagnóstico: *"Inactividad prolongada con riesgo de obsolescencia comercial."* Plan: *"Reunión con el propietario para acordar reducción de valor (-10%) o mejora estética del inmueble."*
  4. **Nivel Crítico ($> 90$ días vacante):** Badge Rojo. Diagnóstico: *"Propiedad estancada. Precio significativamente desfasado respecto al mercado."* Plan: *"Revisión urgente de estrategia, reducción obligada de precio (-15%) o cambio de destino comercial."*

### 4.7. Agenda de Visitas con Control Estricto de Cupos
- **Rutas:** `/propiedades/<id>/visitas` y `/visitas`.
- **Creación de Turnos de Visita:**
  - El agente asigna día, hora, duración estimada (minutos) y **cupo máximo de personas** (ej. 3 personas por turno).
  - **Validación de Inmueble:** Solo se pueden crear turnos para propiedades que se encuentren en estado `disponible`.
  - **Validación de Agenda del Agente:** El sistema rechaza la creación del turno si el agente ya tiene otra visita agendada que se solape en ese rango horario.
- **Inscripción de Visitantes:**
  - Formulario para inscribir interesados con Nombre, Teléfono (WhatsApp), Email y Observaciones particulares.
  - **Control de Cupo Restrictivo:** Si la cantidad de inscriptos alcanza el cupo máximo, el sistema actualiza automáticamente el estado de la agenda a `completo` e impide nuevas inscripciones arrojando un error explicativo.
- **Cancelación de Turnos:** Permite anular turnos coordinados liberando la agenda.

### 4.8. Contratos Legales, Cláusulas Dinámicas e Inmutabilidad
- **Listado de Contratos (`/contratos`):**
  - Visualización de la cartera contractual completa (*Alquileres y Compraventas*).
  - Identificación de N° de Contrato, Inquilino/Comprador, Propiedad, Agente interviniente, honorarios y estado.
- **Solicitud de Nuevo Contrato (`/contratos/nuevo`):**
  - Selecciona un cliente, la propiedad disponible y el agente asignado.
  - Ingreso de monto base, porcentaje total de honorarios de la inmobiliaria (ej. 10% para alquiler, 3% para venta) y porcentaje de comisión que le corresponde al agente comercial (ej. 3%).
  - Posibilidad de adjuntar archivo/documento digital de respaldo (DNI, recibos de sueldo, garantía).
  - **Generación Automática de Cláusulas Legales:** Al crearse la solicitud, el sistema inyecta automáticamente el cuerpo normativo según el tipo de contrato:
    - *Contrato de Alquiler:* 6 cláusulas base (Objeto y Destino, Plazo, Precio y Pago del 1 al 10, Servicios y Expensas, Estado de Conservación, Prohibición de Modificaciones).
    - *Contrato de Compraventa:* 5 cláusulas base (Compraventa y Libre de Gravamen, Precio y Forma de Pago, Escrituración Pública, Posesión Material, Honorarios de Intermediación).
- **Editor de Cláusulas en Estado Solicitado (Borrador):**
  - Permite agregar nuevas cláusulas personalizadas (`/contratos/<nro>/clausulas/agregar`), modificar títulos y redacciones (`/contratos/<nro>/clausulas/<id>/editar`), o eliminarlas.
  - Permite ajustar los porcentajes de comisión de honorarios y del agente (`/contratos/<nro>/comisiones`).
- **Firma y Celebración del Contrato (`/contratos/<nro>/firmar`):**
  - **Principio de Inmutabilidad Legal:** Una vez firmado, el contrato pasa a estado `activo` y la propiedad pasa automáticamente a `alquilada` o `vendida`.
  - **Bloqueo Absoluto:** Queda estrictamente prohibido modificar o eliminar cualquier cláusula, o alterar porcentajes de comisiones en un contrato ya firmado.
- **Vista de Impresión Formal (`/contratos/<nro>/imprimir`):**
  - Plantilla legal estilizada para imprimir en papel o guardar en PDF, con carátula formal, todas las cláusulas numeradas y espacios para firmas y sellos de Locador, Locatario, Martillero e Inmobiliaria.

### 4.9. Reclamos, Roturas Estructurales y Presupuestos para Propietarios
- **Rutas:** `/reclamos`, `/reclamos/nuevo`, `/reclamos/<id>/estado`, `/reclamos/<id>/presupuesto`.
- **Registro de Reclamo Vinculado al Contrato:**
  - El agente registra una rotura o desperfecto estructural sufrido por el inquilino asociándolo directamente al número de contrato activo.
  - El sistema vincula automáticamente la propiedad, el inquilino y el propietario.
  - Clasificación por Rubro: *Estructural / Techos / Muros, Plomería / Humedad, Electricidad, Gas / Calefacción, Cerrajería / Aberturas, Otro*.
  - Nivel de Urgencia: *Baja, Media, Alta, Urgente*.
  - Carga del **Presupuesto Estimado ($)** cotizado para realizar la reparación.
- **Panel de Control de Reclamos (`/reclamos`):**
  - KPIs: Total de Reclamos, Pendientes de Acción, En Reparación / Notificados, Presupuesto Acumulado.
  - Filtros rápidos por estado y buscador por número de contrato.
  - Modal interactivo para actualizar el estado, ajustar el presupuesto definitivo y cargar notas técnicas de resolución.
- **Ciclo de Vida del Reclamo:**
  `Pendiente` ➔ `Informado al Propietario` ➔ `En Reparación` ➔ `Resuelto` / `Desestimado` (asienta automáticamente la fecha de resolución).
- **Informe de Presupuesto Imprimible / PDF para Propietario (`/reclamos/<id>/presupuesto`):**
  - Documento formal listo para emitir y enviar al propietario del inmueble por email o WhatsApp.
  - Detalla los datos del titular, la dirección del inmueble arrendado, el inquilino solicitante, la descripción exhaustiva de la avería, el monto total cotizado de mano de obra y materiales, y el casillero de conformidad para la autorización del arreglo.
- **Acceso Directo desde Contratos:**
  - Botón **"Reclamo"** en la tabla de contratos.
  - Sección completa de historial de reclamos en la ficha de cada contrato (`/contratos/<nro>`).

### 4.10. Finanzas, Cobro de Alquileres, Mora y Boletas en PDF
- **Ruta:** `/finanzas`.
- **Registro de Cobro de Alquiler Inquilino:**
  - Se selecciona el contrato de alquiler activo, el mes correspondiente (*YYYY-MM*), el monto del alquiler y la fecha efectiva de pago.
  - **Soporte de Comprobante Adjunto:** Permite subir el comprobante de transferencia bancaria o recibo en formato PDF, PNG o JPG, el cual se almacena en el servidor y queda disponible para descarga/visualización directa desde la tabla.
- **Regla de Negocio de Vencimiento y Cálculo Automático de Mora:**
  - **1° Vencimiento:** Día 10 del mes correspondiente.
  - **Si el inquilino abona después del día 10:** El sistema calcula los días exactos de retraso ($\text{Días Mora} = \text{Fecha Pago} - \text{Día 10}$) y aplica automáticamente una tasa de recargo por mora del **0.2% diario** sobre el canon de alquiler.
  - Asienta en el registro contable: `monto`, `dias_retraso`, `monto_recargo` y `monto_total_abonado`.
  - En la tabla de cobros se muestra una insignia verde (`A Término`) o un badge de advertencia (`+X días mora ($Recargo)`).
  - **Prevención de Doble Pago:** El sistema rechaza registrar más de un pago para el mismo contrato y período mensual.
- **Boleta / Aviso de Cobro Mensual en PDF (`/finanzas/boleta/<nro>/<mes>`):**
  - Vista de factura/aviso de cobro personalizada para cada inquilino con diseño imprimible (`@media print`).
  - Desglose contable: Alquiler base, Expensas, Tasas, 1° Vencimiento (día 10), 2° Vencimiento estimado con recargo (día 20).
  - Datos de transferencia bancaria de la inmobiliaria (Banco, CBU, Alias, Titular, CUIT).
  - Código de barras de referencia unívoco (`INMO-XXXX-YYYYMM`).
  - Botón flotante para **Imprimir o Guardar en PDF**.

### 4.11. Liquidaciones a Propietarios y Exportaciones
- **Generación Masiva de Liquidaciones:**
  - Exclusivo para Administradores.
  - Al ingresar un período (*YYYY-MM*), el sistema recorre todos los alquileres cobrados de ese mes y genera la liquidación para cada propietario:
    $$\text{Monto Bruto} = \text{Canon Cobrado}$$
    $$\text{Comisión Retenida} = \text{Monto Bruto} \times \left(\frac{\text{Comisión } \%}{100}\right)$$
    $$\text{Monto Neto a Transferir} = \text{Monto Bruto} - \text{Comisión Retenida}$$
  - La liquidación se crea inicialmente en estado `pendiente`.
- **Registro de Transferencia al Propietario:**
  - El administrador presiona **"Registrar Transferencia"** una vez enviada la transferencia bancaria.
  - La liquidación pasa a estado `pagado` y registra la fecha de pago.
- **Exportación de Reportes Financieros en CSV (`/finanzas/exportar/<tipo>`):**
  - Exportación con 1 clic de `cobros_inquilinos` y `liquidaciones_propietarios` para conciliación contable externa en Excel.

### 4.12. Gestión y Alta de Agentes Comerciales (Exclusivo Administrador)
- **Rutas:** `/agentes` y `/agentes/nuevo`.
- **Panel Administrativo de Agentes:**
  - Vista exclusiva para Administradores donde se audita a todos los martilleros y colaboradores de la firma.
  - Tabla con foto/avatar, nombre completo, correo de acceso, rol (*Administrador / Estándar*), matrícula profesional, CUIL, DNI y teléfonos.
- **Alta de Nuevo Agente Comercial:**
  - Formulario protegido para dar de alta nuevos empleados con validación de email, CUIL, matrícula y DNI únicos.
  - Asignación de rol administrativo o comercial estándar.
### 4.13. Notificaciones Automatizadas por Correo Electrónico (SMTP)
- **Alertas de Mora a Inquilinos:**
  - Envío automático/manual de notificaciones a inquilinos cuyos alquileres no registren pago posterior al 1° vencimiento (día 10).
  - Incluye desglose de días de mora, recargos calculados y datos de cuenta bancaria.
  - **Prevención de Spam (`fecha_ultimo_aviso_mora`):** El sistema asienta la fecha del último aviso y no envía recordatorios duplicados en el mismo día.
- **Avisos de Transferencia a Propietarios:**
  - Se disparan de forma automática en el momento exacto en que el administrador asienta el pago de la liquidación al dueño (`registrar_transferencia_propietario`).
  - Notifica canon bruto cobrado, honorarios retenidos y monto neto transferido a su cuenta.
- **Configuración Segura:** Credenciales y servidor SMTP gestionados exclusivamente por variables de entorno (`.env`).

---

## 5. MATRIZ DE REGLAS DE NEGOCIO Y RESTRICCIONES OPERATIVAS

| # | Regla de Negocio | Capa que la Valida | Comportamiento / Restricción |
| :-: | :--- | :-: | :--- |
| **RN-01** | **Disponibilidad para Contratos** | `business/controller.py` | Solo se puede solicitar o firmar un contrato sobre propiedades en estado `disponible`. |
| **RN-02** | **Asignación Agente-Contrato** | `business/controller.py` | El agente que suscribe el contrato debe ser el que tiene la asignación comercial activa sobre la propiedad. |
| **RN-03** | **Multi-propiedad por Agente** | `business/controller.py` | Un agente comercial puede tener asignadas múltiples propiedades simultáneamente sin restricciones. |
| **RN-04** | **Inmutabilidad Contractual** | `business/controller.py` | Una vez firmado el contrato (`activo`), queda estrictamente prohibido agregar, editar o eliminar cláusulas, o modificar honorarios. |
| **RN-05** | **Cupos de Visitas Estrictos** | `business/controller.py` | No se permite inscribir visitantes a un turno cuya cantidad de inscriptos sea igual o superior a `cupo_maximo`. El turno pasa a `completo`. |
| **RN-06** | **No Superposición de Visitas** | `business/controller.py` | Un agente no puede tener dos turnos de visita agendados en horarios superpuestos. |
| **RN-07** | **Visitas solo en Disponibles** | `business/controller.py` | Solo se pueden programar agendas de visita en inmuebles con estado `disponible`. |
| **RN-08** | **Reclamos sobre Contratos Activos** | `business/controller.py` | Solo se pueden asentar reclamos e incidencias sobre contratos que se encuentren en estado `activo`. |
| **RN-09** | **Cálculo de Mora Diaria** | `business/controller.py` | Todo pago de alquiler realizado posterior al día 10 del mes devenga mora automática del 0.2% diario por cada día de retraso. |
| **RN-10** | **Unicidad de Pago Mensual** | `business/controller.py` | No se puede registrar más de un pago de alquiler para el mismo contrato y mismo período (*YYYY-MM*). |
| **RN-11** | **Liquidación Previa al Pago** | `business/controller.py` | No se puede liquidar a un propietario si el inquilino no ha abonado previamente el período correspondiente. |
| **RN-12** | **Permisos de Administrador** | `views/views.py` & `controller.py` | La generación masiva de liquidaciones, transferencias a dueños, exportaciones y gestión de agentes exigen rol `Administrador`. |
| **RN-13** | **Encriptación de Contraseñas** | `business/controller.py` | Las contraseñas de todos los agentes deben almacenarse obligatoriamente hasheadas con algoritmo criptográfico. |
| **RN-14** | **Unicidad de Identificadores** | `datos/db.py` | Email, DNI/Documento, CUIL y Matrícula Profesional deben ser únicos e irrepetibles en la base de datos. |
| **RN-15** | **Control Anti-Spam en Alertas** | `business/controller.py` | Si el contrato ya registró un aviso de mora en el día de la fecha (`fecha_ultimo_aviso_mora == date.today()`), el sistema omite el reenvío. |

---

## 6. CATÁLOGO COMPLETO DE ENDPOINTS Y RUTAS HTTP

### Autenticación y Navegación Base
- `GET /login` / `POST /login`: Formulario e inicio de sesión de agentes.
- `GET /logout`: Cierre de sesión y limpieza de contexto.
- `GET /` / `GET /dashboard`: Tablero principal con métricas y accesos directos.

### Módulo de Clientes
- `GET /clientes`: Listado de clientes e inquilinos.
- `GET /clientes/nuevo` / `POST /clientes/nuevo`: Formulario y alta de clientes.

### Módulo de Propietarios
- `GET /propietarios`: Listado de propietarios.
- `GET /propietarios/nuevo` / `POST /propietarios/nuevo`: Formulario y alta de propietarios.

### Módulo de Propiedades
- `GET /propiedades`: Catálogo general de inmuebles con filtros.
- `GET /propiedades/nueva` / `POST /propiedades/nueva`: Formulario y alta de propiedad.
- `GET /propiedades/<id>`: Ficha técnica detallada del inmueble.
- `GET /propiedades/<id>/asignar` / `POST /propiedades/<id>/asignar`: Asignación de agente comercial a la propiedad.
- `GET /propiedades/inactivas`: Panel estratégico de análisis de vacancia y ranking de días de inactividad.

### Módulo de Visitas y Agendas
- `GET /propiedades/<id>/visitas`: Panel de turnos de visita del inmueble con medidores de cupos e inscriptos.
- `POST /propiedades/<id>/visitas/crear`: Creación de nuevo turno de visita con cupo límite.
- `POST /visitas/<id_agenda>/inscribir`: Inscripción de visitante con validación de sobrecupo.
- `POST /visitas/<id_agenda>/cancelar`: Cancelación de turno de visita.

### Módulo de Contratos y Cláusulas
- `GET /contratos`: Cartera de contratos de locación y compraventa.
- `GET /contratos/nuevo` / `POST /contratos/nuevo`: Solicitud de contrato con autoinyección de cláusulas.
- `GET /contratos/<nro>`: Detalle del contrato, honorarios, desglose de comisiones, cláusulas y reclamos.
- `POST /contratos/<nro>/firmar`: Celebración formal e inmutabilidad legal del contrato.
- `GET /contratos/<nro>/imprimir`: Plantilla de impresión legal para firmas.
- `POST /contratos/<nro>/clausulas/agregar`: Agregar cláusula a contrato solicitado.
- `POST /contratos/<nro>/clausulas/<id>/editar`: Editar cláusula de contrato solicitado.
- `POST /contratos/<nro>/clausulas/<id>/eliminar`: Eliminar cláusula de contrato solicitado.
- `POST /contratos/<nro>/comisiones`: Actualizar porcentajes de honorarios en borrador.

### Módulo de Reclamos y Averías Estructurales
- `GET /reclamos`: Dashboard central de reclamos con KPIs, filtros por estado y modal de actualización.
- `GET /reclamos/nuevo` / `POST /reclamos/nuevo`: Carga de roturas con selector de contrato y presupuesto.
- `POST /reclamos/<id>/estado`: Actualizar estado, notas técnicas y presupuesto definitivo.
- `GET /reclamos/<id>/presupuesto`: Informe formal de presupuesto imprimible y exportable a PDF para el propietario.

### Módulo Financiero y Liquidaciones
- `GET /finanzas`: Tablero financiero general de cobros, liquidaciones y deudas.
- `POST /finanzas/pagos/inquilino`: Registro de cobro con cálculo de mora y comprobante adjunto.
- `GET /finanzas/boleta/<nro>/<mes>`: Emisión de boleta / aviso de cobro mensual en PDF con código de barras.
- `POST /finanzas/liquidaciones/generar`: Generación masiva mensual de liquidaciones *(Admin)*.
- `POST /finanzas/liquidaciones/<id>/pagar`: Registro de transferencia al propietario *(Admin)*.
- `POST /finanzas/notificaciones/mora`: Envío masivo de alertas de mora por email a inquilinos atrasados *(Admin)*.
- `GET /finanzas/exportar/<tipo>`: Descarga de reportes contables en CSV *(Admin)*.

### Módulo de Agentes (Solo Administrador)
- `GET /agentes`: Listado y control de agentes comerciales *(Admin)*.
- `GET /agentes/nuevo` / `POST /agentes/nuevo`: Formulario y alta de agentes con contraseña encriptada *(Admin)*.

---

## 7. FÓRMULAS Y CÁLCULOS FINANCIEROS DEL SISTEMA

### 1. Cálculo de Honorarios y Comisiones Contractuales
$$\text{Honorarios Totales Inmobiliaria} = \text{Monto Contrato} \times \left(\frac{\text{comision\_porcentaje}}{100}\right)$$
$$\text{Comisión Agente Comercial} = \text{Monto Contrato} \times \left(\frac{\text{comision\_agente\_porcentaje}}{100}\right)$$
$$\text{Ganancia Neta Inmobiliaria} = \text{Honorarios Totales} - \text{Comisión Agente}$$

### 2. Cálculo de Mora y Recargo Diario por Pago Fuera de Término
- **Fecha de Vencimiento Estándar:** Día 10 del mes del período a cobrar.
$$\text{Días de Retraso} = \max(0, \text{Fecha Pago} - \text{Fecha Vencimiento})$$
$$\text{Monto de Recargo por Mora} = \text{Monto Alquiler} \times 0.002 \times \text{Días de Retraso}$$
$$\text{Total Efectivamente Abonado} = \text{Monto Alquiler} + \text{Monto de Recargo}$$

### 3. Liquidación Neta a Propietarios Locadores
$$\text{Monto Bruto} = \text{Monto del Canon Cobrado}$$
$$\text{Comisión Inmobiliaria Retenida} = \text{Monto Bruto} \times \left(\frac{\text{Comisión } \%}{100}\right)$$
$$\text{Monto Neto a Transferir al Dueño} = \text{Monto Bruto} - \text{Comisión Inmobiliaria Retenida}$$

---

## 8. DATOS DE PRUEBA Y CREDENCIALES DE ACCESO

El sistema cuenta con un generador automático de datos de muestra (`seed_large_dataset.py`) precargado en la base de datos `tpi_inmobiliaria.db`:

### Credenciales de Inicio de Sesión:
- **Usuario Administrador (Acceso Total):**
  - **Email:** `admin@inmogestion.com`
  - **Contraseña:** `adminpassword`
- **Usuario Agente Comercial Estándar:**
  - **Email:** `martin.gomez@inmogestion.com` (o `valeria.torres@inmogestion.com`)
  - **Contraseña:** `pass123`

### Volumetría de Datos Precargados:
- **5 Agentes:** Administradores y Comerciales con matrículas y CUILs.
- **9 Propietarios y 11 Clientes/Inquilinos** con información completa.
- **14 Propiedades:** En diversas zonas (*Centro, Pichincha, Abasto, Puerto Norte, Fisherton, etc.*) con diferentes fechas de disponibilidad para evaluar el análisis de inactividad.
- **12 Contratos:** Contratos de alquiler y venta activos y solicitudes en borrador con cláusulas.
- **4 Reclamos Estructurales:** Con diferentes rubros (*Plomería, Electricidad, Fachada, Cerrajería*), presupuestos cargados y estados (*Pendientes, En Reparación, Informados al Dueño, Resueltos*).
- **9 Cobros de Alquiler y 9 Liquidaciones:** En períodos `2026-06`, `2026-07`, `2026-08`, con casos a término y casos con mora diaria calculada.
- **3 Agendas de Visita:** Turnos con cupos libres y turnos con cupo completo y visitantes inscriptos.
