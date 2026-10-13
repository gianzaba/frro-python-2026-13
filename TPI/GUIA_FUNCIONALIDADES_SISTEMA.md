# 🏢 Guía Completa de Funcionalidades - InmoGestión (TPI)

**Sistema Web de Gestión Inmobiliaria Integral (Arquitectura en 3 Capas)**  
*Desarrollado en Python Flask, SQLAlchemy y SQLite / PostgreSQL*

---

## 📌 Tabla de Contenidos
1. [Visión General y Roles de Acceso](#1-visión-general-y-roles-de-acceso)
2. [Módulo de Autenticación y Seguridad](#2-módulo-de-autenticación-y-seguridad)
3. [Dashboard Ejecutivo y Métricas en Tiempo Real](#3-dashboard-ejecutivo-y-métricas-en-tiempo-real)
4. [Gestión de Inmuebles y Catálogo Comercial](#4-gestión-de-inmuebles-y-catálogo-comercial)
5. [Análisis Estratégico de Inactividad y Vacancia](#5-análisis-estratégico-de-inactividad-y-vacancia)
6. [Agenda de Visitas con Control Estricto de Cupos](#6-agenda-de-visitas-con-control-estricto-de-cupos)
7. [Gestión de Clientes e Inquilinos](#7-gestión-de-clientes-e-inquilinos)
8. [Gestión de Propietarios (Dueños de Inmuebles)](#8-gestión-de-propietarios-dueños-de-inmuebles)
9. [Contratos Legales, Cláusulas e Inmutabilidad](#9-contratos-legales-cláusulas-e-inmutabilidad)
10. [Módulo de Reclamos, Roturas y Presupuestos](#10-módulo-de-reclamos-roturas-y-presupuestos)
11. [Finanzas, Cobranza con Mora Diaria y Boletas PDF](#11-finanzas-cobranza-con-mora-diaria-y-boletas-pdf)
12. [Liquidaciones a Propietarios y Exportación CSV](#12-liquidaciones-a-propietarios-y-exportación-csv)
13. [Sistema de Alertas y Notificaciones por Correo](#13-sistema-de-alertas-y-notificaciones-por-correo)
14. [Panel de Administración, Agentes y Logs de Auditoría](#14-panel-de-administración-agentes-y-logs-de-auditoría)
15. [Resumen de Reglas de Negocio Implementadas](#15-resumen-de-reglas-de-negocio-implementadas)

---

## 1. Visión General y Roles de Acceso

El sistema está concebido para digitalizar y automatizar todas las actividades del negocio inmobiliario, dividiendo las responsabilidades en dos roles principales:

| Rol | Alcance y Permisos |
| :--- | :--- |
| **Administrador** | Acceso total: gestión de agentes, auditoría de logs del sistema, generación masiva de liquidaciones financieras, confirmación de transferencias a propietarios y exportación de reportes contables en CSV. |
| **Agente Comercial (Estándar)** | Gestión operativa: publicación de inmuebles, atención de clientes y propietarios, coordinación de agendas de visitas, creación y firma de contratos, seguimiento de reclamos y registro de cobros. |

---

## 2. Módulo de Autenticación y Seguridad

- **Login (`/login`):** Acceso seguro mediante correo electrónico y clave.
- **Protección Criptográfica:** Contraseñas protegidas mediante algoritmos de hash irreversibles (`werkzeug.security`).
- **Control de Acceso mediante Decoradores:**
  - `@login_required`: Bloquea el acceso a personas anónimas redirigiéndolas al inicio de sesión.
  - `@admin_required`: Restringe funciones críticas exclusivas para directores/administradores (como pagos y auditoría).
- **Cierre de Sesión (`/logout`):** Cierre y destrucción de la sesión activa del usuario.
- **Páginas de Error Personalizadas:** Vistas dedicadas para errores de autorización `403 Forbidden` y enlaces rotos `404 Not Found`.

---

## 3. Dashboard Ejecutivo y Métricas en Tiempo Real

- **Ubicación:** `/` o `/dashboard`.
- **Indicadores Clave de Desempeño (KPIs):**
  - **Inmuebles en Cartera:** Total de propiedades y desglose inmediato (*Disponibles, Alquiladas, Vendidas*).
  - **Relaciones Comerciales:** Conteo activo de inquilinos/clientes y propietarios registrados.
  - **Contratos Vigentes:** Contratos actualmente activos y solicitudes pendientes en borrador.
  - **Salud Financiera Mensual:** Monto total recaudado en el mes corriente, saldo pendiente de cobro y porcentaje de recaudación.
- **Atajos y Actividad Reciente:** Tablas de contratos recientes, visitas agendadas próximas y accesos rápidos de un solo clic.

---

## 4. Gestión de Inmuebles y Catálogo Comercial

- **Catálogo General (`/propiedades`):**
  - Grilla interactiva con búsqueda y filtros por **Estado** (*Disponible / Alquilada / Vendida*), **Tipo** (*Casa, Departamento, Local, Terreno, Oficina*) y **Zona**.
  - Identificación del agente comercial a cargo de cada propiedad.
- **Alta de Propiedad (`/propiedades/nueva`):**
  - Registro de dirección, tipo de operación, zona, fecha de disponibilidad y asociación obligatoria al propietario.
- **Ficha Técnica y Detalle del Inmueble (`/propiedades/<id>`):**
  - Datos completos, estado comercial y fecha de ingreso.
  - **Historial de Asignaciones Comerciales:** Registro de los agentes asignados en el tiempo.
  - **Historial Contractual:** Vínculo a todos los contratos celebrados sobre dicho inmueble.
- **Asignación de Agente (`/propiedades/<id>/asignar`):**
  - Permite derivar la propiedad a un nuevo corredor comercial.
  - Cierra de forma automática la asignación previa y asienta la nueva.
  - *Regla:* Un agente puede administrar múltiples propiedades en simultáneo.

---

## 5. Análisis Estratégico de Inactividad y Vacancia

- **Ubicación:** `/propiedades/inactivas`.
- **Objetivo Comercial:** Detectar propiedades estancadas en el mercado que llevan semanas o meses sin alquilarse ni venderse, brindando al corredor argumentos objetivos para renegociar con el dueño.
- **Cálculo Automático:** Mide los días exactos de oferta transcurridos desde su fecha de disponibilidad:
  $$\text{Días en Cartera} = \text{Fecha Actual} - \text{Fecha de Disponibilidad}$$
- **Semaforización y Plan de Acción Sugerido:**
  - 🟢 **Bajo ($\le 30$ días):** Período saludable y dentro de los promedios del mercado. Sugerencia: mantener valor y monitorear consultas.
  - 🟡 **Moderado (31 a 60 días):** Interés bajo o desaceleración. Sugerencia: potenciar publicidad y evaluar baja del 5%.
  - 🟠 **Alto (61 a 90 días):** Riesgo de estancamiento prolongado. Sugerencia: reunión con el propietario para proponer rebaja del 10% o mejoras estéticas.
  - 🔴 **Crítico (> 90 días):** Propiedad desfasada con el mercado. Sugerencia: reducción forzosa del 15% o replanteo de destino comercial.

---

## 6. Agenda de Visitas con Control Estricto de Cupos

- **Ubicación:** `/propiedades/<id>/visitas` y `/visitas`.
- **Creación de Turnos de Visita:**
  - Definición de fecha, hora de inicio, duración estimada en minutos y **cupo máximo de personas simultáneas**.
  - *Restricción de Inmueble:* Solo programable en propiedades en estado `disponible`.
  - *Restricción de Agenda:* Valida que el agente no posea otra visita coordinada que se solape en ese rango horario.
- **Inscripción de Interesados:**
  - Carga de visitante con Nombre, Teléfono / WhatsApp, Correo y Notas.
  - **Control de Cupo en Tiempo Real:** Al alcanzar el cupo máximo fijado, el turno cambia su estado a `completo` e impide nuevas inscripciones.
- **Cancelación y Liberación:**
  - Posibilidad de anular turnos o cancelar inscripciones individuales, liberando el cupo inmediatamente.

---

## 7. Gestión de Clientes e Inquilinos

- **Listado Central (`/clientes`):** Vista de todos los compradores e inquilinos registrados.
- **Nuevo Cliente (`/clientes/nuevo`):** Formulario con validación estricta para evitar duplicidad de documento (DNI, CUIT, Pasaporte) y correo electrónico.

---

## 8. Gestión de Propietarios (Dueños de Inmuebles)

- **Listado Central (`/propietarios`):** Directorio de locadores y vendedores.
- **Nuevo Propietario (`/propietarios/nuevo`):** Alta con verificación de datos de contacto y unicidad de identificación para la posterior liquidación bancaria de fondos.

---

## 9. Contratos Legales, Cláusulas e Inmutabilidad

- **Listado General (`/contratos`):** Matriz de contratos de locación y compraventa clasificados por estado (*Solicitado, Activo, Finalizado*).
- **Solicitud de Nuevo Contrato (`/contratos/nuevo`):**
  - Vinculación de cliente, propiedad disponible y agente a cargo.
  - Carga del canon/valor, porcentaje de honorarios de la inmobiliaria y comisión del agente comercial.
  - Soporte para subir archivos digitales de respaldo (DNI escaneado, garantías propietarias, recibos de sueldo).
  - **Inyección Automática de Cláusulas Base:**
    - *Alquileres:* 6 cláusulas predeterminadas (Destino habitacional/comercial, Plazo legal, Pago del 1 al 10, Servicios y expensas, Mantenimiento y Prohibición de cesión).
    - *Compraventas:* 5 cláusulas predeterminadas (Libre gravamen, Precio pactado, Escrituración traslativa de dominio, Posesión y Honorarios).
- **Editor de Cláusulas en Borrador:**
  - Mientras el contrato está en estado `solicitado`, se pueden agregar nuevas cláusulas, editar títulos y redacciones, o eliminarlas.
  - Modificación de porcentajes de honorarios.
- **Firma y Principio de Inmutabilidad Legal (`/contratos/<nro>/firmar`):**
  - Al firmarse, el contrato pasa a `activo` y el inmueble pasa automáticamente a `alquilada` o `vendida`.
  - **Bloqueo Total:** A partir de la firma, el sistema prohíbe de forma estricta cualquier cambio, borrado de cláusulas o modificación de comisiones.
- **Plantilla de Impresión Legal (`/contratos/<nro>/imprimir`):**
  - Vista formal optimizada para imprimir en papel o guardar en PDF, con formato notarial, articulado legal completo y áreas para rúbrica de locador, locatario y martillero.

---

## 10. Módulo de Reclamos, Roturas y Presupuestos

- **Ubicación:** `/reclamos`, `/reclamos/nuevo` y ficha de contratos.
- **Registro de Avería Vinculada a Contrato:**
  - Se vincula directamente al número de contrato activo, reconociendo en automático la propiedad, el inquilino y el dueño.
  - Clasificación por rubro: *Plomería / Humedad, Electricidad, Gas / Calefacción, Estructural / Techos, Cerrajería, etc.*
  - Nivel de Urgencia: *Baja, Media, Alta o Urgente*.
  - Carga del **Presupuesto Estimado ($)** cotizado para el arreglo.
- **Ciclo de Estados:**
  $$\text{Pendiente} \longrightarrow \text{Informado al Propietario} \longrightarrow \text{En Reparación} \longrightarrow \text{Resuelto / Desestimado}$$
- **Emisión de Presupuesto Formal en PDF (`/reclamos/<id>/presupuesto`):**
  - Generación de un informe técnico formal para enviar al propietario por WhatsApp o email con el detalle de los materiales, mano de obra cotizada y espacio para su firma de autorización.

---

## 11. Finanzas, Cobranza con Mora Diaria y Boletas PDF

- **Ubicación:** `/finanzas`.
- **Registro de Cobro de Alquileres:**
  - Selección de contrato activo, mes a cobrar (*YYYY-MM*), monto y fecha real de pago.
  - **Carga de Comprobante Adjunto:** Soporta archivos PDF o imágenes (PNG, JPG) de las transferencias recibidas, visualizables directamente desde la tabla contable.
  - **Prevención de Duplicidad:** El sistema bloquea el intento de registrar dos cobros para el mismo contrato y mismo mes.
- **Cálculo Automático de Mora Diaria (Post Día 10):**
  - Vencimiento base fijado el día 10 del mes.
  - A partir del día 11, calcula los días exactos de atraso y aplica un **recargo por mora del 0.2% diario**:
    $$\text{Recargo} = \text{Monto Alquiler} \times 0.002 \times \text{Días de Atraso}$$
    $$\text{Total Cobrado} = \text{Monto Alquiler} + \text{Recargo}$$
  - En la tabla se discrimina claramente entre pagos *"A Término"* y pagos con *"X días de mora"*.
- **Aviso de Cobro / Boleta Mensual en PDF (`/finanzas/boleta/<nro>/<mes>`):**
  - Comprobante con diseño formal imprimible.
  - Detalle de vencimientos (1° y 2° vencimiento con recargo), datos bancarios de la inmobiliaria (CBU/Alias) y código de barras de seguimiento único.

---

## 12. Liquidaciones a Propietarios y Exportación CSV

- **Generación Masiva Mensual:**
  - Función exclusiva del Administrador.
  - Recorre los alquileres percibidos del mes y computa automáticamente la liquidación por propietario:
    $$\text{Neto a Transferir} = \text{Canon Bruto Cobrado} - \text{Honorarios Inmobiliarios}$$
  - Queda inicialmente asentada en estado `pendiente`.
- **Confirmación de Transferencia Bancaria:**
  - El administrador confirma el pago al propietario mediante el botón *"Registrar Transferencia"*, pasando el estado a `pagado` con su fecha de liquidación.
- **Exportación Contable en CSV (`/finanzas/exportar/<tipo>`):**
  - Permite descargar con un clic las tablas de **Cobros de Inquilinos** y **Liquidaciones a Propietarios** para su análisis en Excel o sistemas contables externos.

---

## 13. Sistema de Alertas y Notificaciones por Correo

- **Alertas de Mora Automatizadas:**
  - Posibilidad de enviar avisos de mora masivos o individuales a los inquilinos que registren pagos atrasados.
  - Desglose informativo del monto adeudado, recargos y datos de la cuenta recaudadora.
- **Filtro Anti-Spam:**
  - El sistema guarda la fecha del último recordatorio emitido y bloquea envíos duplicados en la misma jornada.
- **Avisos de Transferencia a Propietarios:**
  - Disparo de aviso automático al momento en que el administrador acredita la liquidación neta en la cuenta del propietario.

---

## 14. Panel de Administración, Agentes y Logs de Auditoría

- **Directorio de Agentes Comerciales (`/agentes`):**
  - Vista restringida a Administradores para dar de alta nuevos corredores comerciales o directores con sus matrículas, CUIL, teléfonos y credenciales cifradas.
- **Logs de Auditoría del Sistema (`/admin/audit-logs`):**
  - Registro cronológico inmutable de todas las acciones operativas sensibles (creación de contratos, firmas, cancelaciones, modificaciones y pagos), indicando fecha/hora exacta, agente interviniente y detalle del evento.

---

## 15. Resumen de Reglas de Negocio Implementadas

1. **RN-01 (Propiedades Disponibles):** Solo se pueden crear turnos de visita o solicitar contratos sobre inmuebles en estado `disponible`.
2. **RN-02 (Asignación Activa):** El agente que suscribe el contrato debe ser el comercial formalmente asignado al inmueble.
3. **RN-03 (Multi-gestión):** Un agente puede comercializar simultáneamente cuantas propiedades tenga asignadas.
4. **RN-04 (Inmutabilidad Contractual):** Prohibido alterar o suprimir cláusulas u honorarios en contratos en estado `activo`.
5. **RN-05 (Límite de Cupo en Visitas):** Bloqueo automático de inscripciones cuando el cupo llega al límite configurado.
6. **RN-06 (No Superposición Horaria):** Se rechaza la creación de visitas que coincidan con la franja horaria de otra visita ya agendada para el mismo agente.
7. **RN-07 (Reclamos en Contratos Activos):** No se admiten reclamos sobre contratos en borrador o finalizados.
8. **RN-08 (Mora Diaria 0.2%):** Computada de forma automática e invariable sobre cánones abonados después del día 10.
9. **RN-09 (Unicidad de Cobro Mensual):** Impide duplicar el registro de alquiler para el mismo contrato y mes.
10. **RN-10 (Seguridad en Liquidaciones):** No es posible liquidar fondos al propietario si el inquilino no ha abonado previamente el período.
11. **RN-11 (Auditoría y Roles):** Las acciones financieras de egreso y gestión de agentes están limitadas por middleware al rol `Administrador`.
12. **RN-12 (Cartera Propia por Agente):** Cada agente comercial estándar visualiza y gestiona exclusivamente sus propios clientes y propietarios registrados. El Administrador conserva vista global.
13. **RN-13 (Cancelación Concurrente de Solicitudes):** Al firmarse una solicitud de contrato sobre un inmueble, cualquier otra solicitud pendiente en estado `solicitado` para esa misma propiedad pasa automáticamente a estado `cancelado` con registro de auditoría.
14. **RN-14 (Traspaso de Titularidad tras Venta):** Cuando una propiedad vendida pasa a ser administrada nuevamente, el sistema permite traspasar la titularidad al comprador (incorporándolo como Propietario si no lo era), archivando el contrato anterior como `finalizado` y reactivando la propiedad como `disponible`.
