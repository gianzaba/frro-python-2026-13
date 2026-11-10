# 📱 5. Catálogo Completo de Funcionalidades del Sistema

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 📑 Módulos del Sistema

1. [Autenticación, Seguridad y Roles (RBAC)](#1-autenticación-seguridad-y-roles-rbac)
2. [Dashboard Ejecutivo y Métricas en Tiempo Real](#2-dashboard-ejecutivo-y-métricas-en-tiempo-real)
3. [Catálogo de Inmuebles y Comercialización](#3-catálogo-de-inmuebles-y-comercialización)
4. [Análisis Estratégico de Inactividad y Vacancia](#4-análisis-estratégico-de-inactividad-y-vacancia)
5. [Agenda de Visitas con Control Estricto de Cupos](#5-agenda-de-visitas-con-control-estricto-de-cupos)
6. [Gestión de Clientes e Inquilinos (Cartera Aislada)](#6-gestión-de-clientes-e-inquilinos-cartera-aislada)
7. [Gestión de Propietarios (Dueños de Inmuebles)](#7-gestión-de-propietarios-dueños-de-inmuebles)
8. [Contratos Legales, Cláusulas e Inmutabilidad](#8-contratos-legales-cláusulas-e-inmutabilidad)
9. [Aprobación del Propietario y Cancelación Concurrente](#9-aprobación-del-propietario-y-cancelación-concurrente)
10. [Módulo de Reclamos, Roturas y Presupuestos PDF](#10-módulo-de-reclamos-roturas-y-presupuestos-pdf)
11. [Finanzas: Cobranza con Mora Diaria y Boletas PDF](#11-finanzas-cobranza-con-mora-diaria-y-boletas-pdf)
12. [Liquidaciones a Propietarios y Exportación CSV](#12-liquidaciones-a-propietarios-y-exportación-csv)
13. [Traspaso de Titularidad tras Compraventa](#13-traspaso-de-titularidad-tras-compraventa)
14. [Sistema de Notificaciones por Correo Electrónico](#14-sistema-de-notificaciones-por-correo-electrónico)
15. [Logs de Auditoría Inmutable](#15-logs-de-auditoría-inmutable)

---

## 1. Autenticación, Seguridad y Roles (RBAC)

El sistema provee control de acceso basado en roles con dos perfiles claramente diferenciados:

| Perfil / Rol | Alcance y Permisos |
| :--- | :--- |
| **Administrador** | - Control total de la inmobiliaria.<br>- Alta y gestión de agentes comerciales.<br>- Visualización y auditoría global de toda la cartera de clientes, propietarios y contratos.<br>- Generación masiva de liquidaciones a propietarios.<br>- Confirmación y registro de transferencias bancarias a dueños.<br>- Envío masivo de alertas de mora por correo.<br>- Exportación contable en formato CSV.<br>- Visualización del log inmutable de auditoría. |
| **Agente Comercial (Estándar)** | - Gestión operativa y comercial cotidiana.<br>- **Aislamiento de Cartera:** visualiza y administra exclusivamente sus propios clientes y propietarios.<br>- Publicación y edición de inmuebles asignados.<br>- Coordinación de visitas con control de cupos.<br>- Solicitud, negociación de cláusulas y firma de contratos.<br>- Registro de reclamos e incidencias de inquilinos.<br>- Registro de cobros mensuales y emisión de boletas. |

- **Inicio de Sesión (`/login`):** Validación segura contra hashes criptográficos irreversibles (`pbkdf2:sha256`).
- **Control de Sesión:** Cookies de sesión seguras (`HttpOnly`, `SameSite=Lax`).
- **Protección de Vistas:** Mediante los decoradores `@login_required` y `@admin_required`.
- **Manejo Personalizado de Errores HTTP:** Páginas dedicadas para accesos denegados (`403 Forbidden`) y recursos inexistentes (`404 Not Found`).

---

## 2. Dashboard Ejecutivo y Métricas en Tiempo Real

- **Ruta:** `/` o `/dashboard`.
- **Tarjetas de KPIs Principales:**
  - **Inmuebles en Cartera:** Total general discriminado en *Disponibles*, *Alquiladas* y *Vendidas*.
  - **Relaciones Comerciales:** Conteo activo de clientes e inquilinos registrados.
  - **Contratos Vigentes:** Contratos formalmente activos y solicitudes en trámite.
  - **Recaudación Mensual:** Monto total cobrado en el mes en curso frente al total pendiente de cobro, con cálculo automático de eficiencia porcentual de cobranza.
- **Actividad Reciente y Accesos Rápidos:** Accesos directos para emisión de contratos, agendamiento de turnos, registro de cobros e inspección de reclamos urgentes.

---

## 3. Catálogo de Inmuebles y Comercialización

- **Catálogo General (`/propiedades`):**
  - Grilla interactiva con búsqueda en tiempo real y filtros multicriterio por:
    - **Estado:** *Disponible*, *Alquilada*, *Vendida*.
    - **Tipo de Inmueble:** *Casa*, *Departamento*, *Local*, *Terreno*, *Oficina*.
    - **Tipo de Operación:** *Alquiler* o *Venta*.
    - **Zona Geográfica:** *Centro*, *Pichincha*, *Puerto Norte*, *Fisherton*, etc.
  - Indicación visual del agente comercial asignado a cada inmueble.
- **Alta de Propiedad (`/propiedades/nueva`):**
  - Formulario con dirección, tipo de inmueble, tipo de operación, zona, fecha de disponibilidad y selección obligatoria del propietario.
- **Ficha Técnica Detallada (`/propiedades/<id>`):**
  - Datos completos de la propiedad y estado comercial.
  - **Historial de Comercialización:** Registro cronológico de todos los agentes que tuvieron asignada la propiedad.
  - **Historial Contractual:** Vínculo a todos los contratos celebrados sobre el inmueble.
- **Asignación de Agente (`/propiedades/<id>/asignar`):**
  - Permite derivar la propiedad a un nuevo corredor comercial.
  - Finaliza automáticamente la asignación activa anterior y asienta la nueva con marca temporal.
  - *Flexibilidad:* Un agente puede administrar múltiples propiedades en simultáneo sin restricciones.

---

## 4. Análisis Estratégico de Inactividad y Vacancia

- **Ruta:** `/propiedades/inactivas`.
- **Propósito de Negocio:** Brinda a los martilleros una herramienta analítica objetiva para detectar propiedades estancadas en el mercado que llevan semanas o meses sin concretar operaciones, facilitando fundamentar bajas de valor ante los dueños.
- **Cálculo de Días en Oferta:**
  $$\text{Días Vacante} = \text{Fecha Actual} - \text{Fecha de Disponibilidad}$$
- **Semaforización y Plan de Acción Sugerido:**

| Nivel de Vacancia | Días Vacante | Badge Visual | Diagnóstico Comercial | Plan de Acción Sugerido |
| :--- | :---: | :---: | :--- | :--- |
| **Bajo** | $\le 30$ días | 🟢 Verde | Período de comercialización saludable y dentro del promedio del mercado. | Mantener precio y monitorear volumen de consultas. |
| **Moderado** | $31 - 60$ días | 🟡 Amarillo | Tiempo en oferta superior al promedio. Interés moderado. | Reforzar difusión en portales destacados y evaluar ajuste sugerido (-5%). |
| **Alto** | $61 - 90$ días | 🟠 Naranja | Inactividad prolongada con riesgo de obsolescencia comercial. | Reunión con el propietario para acordar reducción de valor (-10%) o mejora estética. |
| **Crítico** | $> 90$ días | 🔴 Rojo | Propiedad estancada. Precio significativamente desfasado respecto al mercado. | Revisión urgente de estrategia, reducción obligada (-15%) o cambio de destino comercial. |

---

## 5. Agenda de Visitas con Control Estricto de Cupos

- **Rutas:** `/propiedades/<id>/visitas` y `/visitas` (Agenda Global).
- **Creación de Turnos de Visita:**
  - El agente asigna día, hora de inicio, duración estimada en minutos y **cupo máximo de personas simultáneas** (ej. 3 personas).
  - *Validación 1:* Solo programable en propiedades en estado `disponible`.
  - *Validación 2 (No Superposición Horaria):* El sistema rechaza la creación del turno si el agente ya tiene otra visita agendada que se solape en ese rango horario.
- **Inscripción de Visitantes:**
  - Formulario para inscribir interesados con Nombre, Teléfono/WhatsApp, Correo y Observaciones.
  - **Control de Cupo Restrictivo:** Al alcanzar el cupo fijado, el turno cambia automáticamente a estado `completo` e impide nuevas inscripciones.
- **Cancelación y Liberación:** Permite cancelar turnos o anular inscripciones, liberando el cupo inmediatamente.

---

## 6. Gestión de Clientes e Inquilinos (Cartera Aislada)

- **Listado Central (`/clientes`):** Vista de compradores e inquilinos registrados.
- **Aislamiento de Cartera Comercial:**
  - Los agentes estándar solo pueden ver y gestionar los clientes que ellos mismos dieron de alta (`id_agente_creador == session['agente_id']`).
  - Los administradores poseen visión global de la cartera completa de la firma.
- **Alta de Nuevo Cliente (`/clientes/nuevo`):** Formulario con validación de unicidad de documento (`tipo_doc + nro_doc`) y correo electrónico.

---

## 7. Gestión de Propietarios (Dueños de Inmuebles)

- **Listado Central (`/propietarios`):** Directorio de locadores y vendedores.
- **Aislamiento de Cartera:** Al igual que con clientes, cada agente comercial gestiona sus propios propietarios registrados, manteniendo el Administrador la supervisión general.
- **Alta de Propietario (`/propietarios/nuevo`):** Verificación de datos de contacto y datos bancarios para futuras transferencias de liquidaciones.

---

## 8. Contratos Legales, Cláusulas e Inmutabilidad

- **Listado de Contratos (`/contratos`):** Cartera completa de locaciones y compraventas clasificada por estado (`solicitado`, `activo`, `finalizado`, `cancelado`).
- **Solicitud de Contrato (`/contratos/nuevo`):**
  - Vincula cliente, propiedad disponible y agente comercial responsable.
  - Define monto del acuerdo, porcentaje de honorarios de la inmobiliaria (ej. 10% en alquiler, 3% en venta) y comisión del agente (ej. 3%).
  - Carga y evaluación de garantías y recibos de sueldo con soporte de adjuntos digitales.
  - **Inyección Automática de Cláusulas Base:**
    - **Contratos de Alquiler (6 cláusulas):** Objeto y Destino, Plazo Legal, Precio y Pago del 1 al 10, Servicios y Expensas, Mantenimiento y Conservación, Prohibición de Cesión.
    - **Contratos de Compraventa (5 cláusulas):** Compraventa Libre de Gravamen, Precio Pactado, Escrituración Pública, Posesión Material, Honorarios de Intermediación.
- **Editor de Cláusulas en Borrador:**
  - Mientras el contrato está en estado `solicitado`, permite agregar nuevas cláusulas (`/clausulas/agregar`), editar redacciones (`/clausulas/<id>/editar`) o eliminarlas.
  - Permite reajustar los porcentajes de comisión (`/contratos/<nro>/comisiones`).
- **Firma y Principio de Inmutabilidad Legal (`/contratos/<nro>/firmar`):**
  - Al firmarse, el contrato pasa a estado `activo` y la propiedad pasa automáticamente a `alquilada` o `vendida`.
  - **Bloqueo Absoluto:** A partir de la firma, el sistema prohíbe de forma estricta cualquier modificación de cláusulas u honorarios.
- **Plantilla de Impresión Legal (`/contratos/<nro>/imprimir`):**
  - Formato notarial formal con articulado legal completo y espacios de rúbrica para Locador, Locatario, Martillero e Inmobiliaria.

---

## 9. Aprobación del Propietario y Cancelación Concurrente

- **Decisión del Propietario:**
  - El sistema permite registrar la decisión del propietario (`aprobado`, `rechazado`, `pendiente`) tras evaluar las garantías y recibos del interesado (`/contratos/<nro>/decision-propietario`).
  - Si el propietario rechaza la solicitud, esta no puede firmarse y se asienta el motivo en las observaciones.
- **Cancelación Concurrente de Solicitudes:**
  - Si existen múltiples solicitudes en borrador sobre la misma propiedad disponible, en el momento exacto en que una de ellas es firmada, el sistema **cancela automáticamente todas las demás solicitudes pendientes** sobre ese inmueble y registra el evento en auditoría.

---

## 10. Módulo de Reclamos, Roturas y Presupuestos PDF

- **Rutas:** `/reclamos`, `/reclamos/nuevo`, `/reclamos/<id>/estado` y `/reclamos/<id>/presupuesto/pdf`.
- **Registro de Reclamo Vinculado al Contrato:**
  - Se vincula directamente al número de contrato activo, reconociendo automáticamente la propiedad, el inquilino y el dueño titular.
  - Clasificación por rubro: *Plomería / Humedad*, *Electricidad*, *Gas / Calefacción*, *Estructural / Techos*, *Cerrajería*, *Otros*.
  - Nivel de Urgencia: *Baja*, *Media*, *Alta*, *Urgente*.
  - Carga del **Presupuesto Estimado ($)** cotizado para efectuar la reparación.
- **Ciclo de Estados:**
  $$\text{Pendiente} \longrightarrow \text{Informado al Propietario} \longrightarrow \text{En Reparación} \longrightarrow \text{Resuelto / Desestimado}$$
- **Emisión de Presupuesto Formal en PDF:**
  - Generación de informe técnico formal vectorizado con ReportLab listo para enviar al dueño por WhatsApp o email con el detalle de materiales, mano de obra y casillero de conformidad.

---

## 11. Finanzas: Cobranza con Mora Diaria y Boletas PDF

- **Ruta:** `/finanzas`.
- **Registro de Cobro de Alquiler:**
  - Selección de contrato activo, período (*YYYY-MM*), canon y fecha efectiva de pago.
  - **Carga de Comprobante Adjunto:** Soporta archivos PDF o imágenes (PNG, JPG) de transferencias bancarias, visualizables desde la tabla contable.
  - **Prevención de Doble Pago:** Bloquea registrar más de un cobro para el mismo contrato y mismo mes.
- **Regla de Vencimiento y Cálculo Automático de Mora:**
  - **1° Vencimiento:** Día 10 del mes correspondiente.
  - **Cálculo de Recargo Post Día 10 (0.2% diario):**
    $$\text{Días de Atraso} = \max(0, \text{Fecha Pago} - \text{Día 10})$$
    $$\text{Recargo por Mora} = \text{Monto Alquiler} \times 0.002 \times \text{Días de Atraso}$$
    $$\text{Total Efectivamente Abonado} = \text{Monto Alquiler} + \text{Recargo por Mora}$$
  - En la grilla se discrimina visualmente: badge verde `A Término` o badge de advertencia `+X días mora ($Recargo)`.
- **Boleta Mensual / Aviso de Cobro en PDF (`/finanzas/boleta/<nro>/<mes>/pdf`):**
  - Documento formal con código de barras `Code128`, desglose de vencimientos (1° y 2° vencimiento), datos bancarios de la agencia y firma autorizada.

---

## 12. Liquidaciones a Propietarios y Exportación CSV

- **Generación Masiva de Liquidaciones (Solo Admin):**
  - El administrador ingresa el período (*YYYY-MM*) y el sistema genera automáticamente las liquidaciones de todos los alquileres cobrados:
    $$\text{Monto Bruto} = \text{Canon Percibido}$$
    $$\text{Comisión Inmobiliaria} = \text{Monto Bruto} \times \left(\frac{\text{Comisión } \%}{100}\right)$$
    $$\text{Monto Neto a Transferir} = \text{Monto Bruto} - \text{Comisión Inmobiliaria}$$
  - Queda asentada en estado `pendiente`.
  - **Seguridad Financiera:** No se puede liquidar un período si el inquilino no ha abonado previamente.
- **Confirmación de Transferencia Bancaria (Solo Admin):**
  - Al pulsar "Registrar Transferencia", la liquidación pasa a estado `pagado` y asienta la fecha de pago.
- **Exportación Contable en CSV (`/finanzas/exportar/<tipo>`):**
  - Descarga directa con 1 clic de los reportes de *Cobros de Inquilinos* y *Liquidaciones a Propietarios* para conciliación externa en Excel.

---

## 13. Traspaso de Titularidad tras Compraventa

- **Flujo de Traspaso:**
  - Cuando un inmueble vendido mediante contrato de compraventa pasa a ser administrado nuevamente por la inmobiliaria, el sistema permite transferir la titularidad registral al comprador.
  - Si el comprador no estaba registrado como propietario, el sistema lo crea automáticamente como nuevo `Propietario`.
  - Actualiza `id_propietario` en el inmueble, archiva el contrato anterior como `finalizado`, reactiva la propiedad como `disponible` y asienta el evento en auditoría.

---

## 14. Sistema de Notificaciones por Correo Electrónico

- **Alertas Masivas de Mora:** Notifica a inquilinos con cánones atrasados posterior al día 10 con desglose de días de mora, recargos y CBU recaudadora.
- **Filtro Anti-Spam (`fecha_ultimo_aviso_mora`):** Evita reenviar más de un recordatorio al mismo inquilino en la misma jornada.
- **Avisos de Liquidación a Propietarios:** Se dispara automáticamente en el instante en que el Administrador confirma la transferencia de su renta.

---

## 15. Logs de Auditoría Inmutable

- **Ruta:** `/admin/audit-logs` (Exclusivo Administrador).
- **Registro Inmutable de Eventos:**
  - Asienta cronológicamente cada acción sensible: creación de contratos, firmas, cancelaciones concurrentes, transferencias financieras, decisiones de dueños y altas de agentes.
  - Campos registrados: fecha y hora exacta, agente interviniente, entidad afectada (`contrato`, `pago`, `propiedad`, etc.), ID del registro y descripción detallada del cambio.

