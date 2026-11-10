# 🏢 1. Problema para el cual creamos el Sistema y Objetivos

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 📌 Contexto y Diagnóstico del Negocio Inmobiliario

El sector inmobiliario contemporáneo opera en un entorno altamente dinámico y regulado, donde convergen múltiples actores con intereses diversos:
- **Propietarios (Locadores / Vendedores):** Exigen transparencia en la liquidación de sus rentas, cobros en fecha, cuidado de sus propiedades e informes detallados ante desperfectos o averías estructurales.
- **Inquilinos y Compradores (Clientes):** Demandan agilidad en la coordinación de visitas, claridad en los términos contractuales, boletas de cobro discriminadas y canales formales para canalizar incidencias edilicias.
- **Corredores y Agentes Inmobiliarios:** Requieren gestionar su propia cartera de clientes, coordinar agendas de visitas sin superposiciones horarias y realizar seguimiento de sus comisiones por operaciones celebradas.
- **Directores y Administradores de la Inmobiliaria:** Necesitan supervisar la rentabilidad del negocio en tiempo real, auditar las acciones de su personal, controlar la morosidad y contar con seguridad jurídica ante compromisos asumidos.

### Problemáticas Detectadas en Agencias Tradicionales

En la mayoría de las pequeñas y medianas inmobiliarias, estas operaciones se realizan mediante planillas de cálculo dispersas (Excel), anotaciones informales en papel y canales de mensajería desestructurados (WhatsApp). Este enfoque genera graves ineficiencias operativas y riesgos legales:

1. **Desorganización en la Captación y Visitas de Inmuebles:**
   - Superposición de turnos para un mismo agente inmobiliario.
   - Ausencia de control en el aforo o cupo máximo de interesados por visita, provocando aglomeraciones y una mala experiencia comercial.
   - Falta de un registro unificado de interesados y de asistencia a las visitas comerciales.

2. **Propiedades Estancadas y Vacancia Prolongada:**
   - Pérdida de seguimiento temporal sobre los inmuebles en oferta.
   - Carencia de métricas y diagnósticos objetivos para advertir cuándo un inmueble lleva demasiados días vacante en el mercado y requiere una baja sugerida de precio o un cambio de estrategia con el propietario.

3. **Inseguridad Jurídica y Alteración de Contratos:**
   - Redacción manual de contratos propensa a omisiones de cláusulas legales fundamentales (destino habitacional, penalidades, prórrogas, indexación).
   - Riesgo de manipulación posterior o alteración unilateral de acuerdos una vez suscriptos por las partes.
   - Gestión desordenada de la documentación digital de respaldo (DNI, escrituras, garantías propietarias y recibos de sueldo).
   - Conflictos cuando existen solicitudes concurrentes sobre un mismo inmueble sin un criterio automático de resolución.

4. **Descontrol Financiero, Cobranza y Mora:**
   - Cobros registrados manualmente sin una fórmula uniforme y transparente de cálculo de intereses por mora tras el vencimiento legal.
   - Emisión deficiente de boletas o comprobantes de cobro con código de seguimiento y discriminación clara de conceptos.
   - Pérdida de comprobantes de pago aportados por los inquilinos.

5. **Complejidad y Retrasos en Liquidaciones a Propietarios:**
   - Dificultad para calcular masivamente los honorarios retenidos por la agencia y el saldo neto exacto que debe transferirse a cada dueño.
   - Riesgo de transferir fondos al propietario antes de que el inquilino haya cancelado efectivamente su alquiler.
   - Falta de notificaciones automáticas que informen fehacientemente al locador cuando su liquidación fue transferida.

6. **Gestión Informal de Reclamos y Averías:**
   - Reclamos por humedades, filtraciones o roturas eléctricas canalizados verbalmente, sin registro del contrato asociado, urgencia ni presupuesto de reparación.
   - Ausencia de un informe formal o presupuesto imprimible para solicitar la autorización del dueño antes de contratar proveedores técnicos.

7. **Ausencia de Aislamiento de Cartera y Falta de Auditoría:**
   - Todos los agentes acceden indiscriminadamente a los clientes de sus pares, generando roces comerciales internos.
   - Imposibilidad de saber quién dio de alta, modificó o firmó un documento sensible ante discrepancias o auditorías.

---

## 🎯 Solución Propuesta: InmoGestión B2B

Para dar respuesta definitiva a esta problemática, se concibió y desarrolló **InmoGestión B2B**: una plataforma web integral basada en una sólida **Arquitectura en 3 Capas**, programada íntegramente en Python con Flask y SQLAlchemy.

El sistema digitaliza y automatiza el ciclo de vida operativo, comercial, legal y financiero de la inmobiliaria bajo estándares de seguridad informática y confiabilidad contable.

```
       CICLO DE VIDA INTEGRAL EN INMOGESTIÓN B2B
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  1. CAPTACIÓN  │ ──> │  2. DIFUSIÓN   │ ──> │   3. VISITAS   │
│ Alta Inmueble  │     │ Análisis de    │     │ Agenda con     │
│ y Propietario  │     │ Vacancia       │     │ Cupos Límite   │
└────────────────┘     └────────────────┘     └────────────────┘
                                                       │
                                                       ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ 6. LIQUIDACIÓN │ <── │  5. COBRANZA   │ <── │  4. CONTRATO   │
│ Transferencia  │     │ Canon con Mora │     │ Cláusulas e    │
│ Neta a Dueño   │     │ Diaria y PDF   │     │ Inmutabilidad  │
└────────────────┘     └────────────────┘     └────────────────┘
```

---

## 🚀 Objetivos del Proyecto

### Objetivo General
Desarrollar una aplicación web escalable, segura y portable que optimice la operativa de una agencia inmobiliaria mediante la automatización de procesos clave, el cumplimiento estricto de reglas de negocio y una estricta separación de responsabilidades en tres capas de software.

### Objetivos Específicos
1. **Separación de Responsabilidades:** Implementar de forma rigurosa la separación entre Capa de Presentación (Flask / Jinja2), Capa de Negocio (Controlador y Entidades de Dominio) y Capa de Datos (SQLAlchemy ORM con soporte dual SQLite/PostgreSQL).
2. **Seguridad y Control de Acceso Basado en Roles (RBAC):** Proveer mecanismos de autenticación robustos mediante encriptación de contraseñas (`pbkdf2:sha256`) y delimitación de privilegios entre Administradores y Agentes Comerciales Estándar.
3. **Aislamiento de Carteras Comerciales:** Asegurar que cada agente estándar administre y visualice exclusivamente sus propios clientes y propietarios, garantizando la privacidad y el orden interno.
4. **Garantía de Inmutabilidad Legal:** Implementar validaciones de negocio que impidan cualquier edición o supresión de cláusulas o comisiones una vez formalizado un contrato.
5. **Automatización del Cálculo Financiero de Mora:** Diseñar un motor de cálculo que determine con precisión cronológica los días de atraso y los recargos diarios (0.2% por jornada) aplicables sobre el canon locativo post día 10.
6. **Liquidaciones Automatizadas:** Computar liquidaciones netas a propietarios mediante retención automática de honorarios pactados, condicionadas a la efectiva acreditación previa del pago del inquilino.
7. **Gestión Estructurada de Reclamos e Incidencias:** Proveer un flujo de estados para averías estructurales, emitiendo presupuestos formales para la aprobación del dueño.
8. **Generación Programática de Documentos Digitales:** Proveer boletas de cobro con código de barras y presupuestos técnicos listos para impresión y guardado en PDF (ReportLab).
9. **Trazabilidad y Auditoría:** Registrar en un log inmutable del sistema cada operación crítica (altas, firmas, cancelaciones, transferencias y rechazos), identificando autor, fecha y detalle.

