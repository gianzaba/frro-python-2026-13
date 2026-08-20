# InmoGestión - Sistema de Gestión Inmobiliaria

**InmoGestión** es un sistema web integral diseñado para optimizar la administración operativa, comercial y financiera de una agencia inmobiliaria. Permite gestionar propiedades, clientes, propietarios, agentes inmobiliarios, contratos de alquiler/venta y la contabilidad mensual de cobros y liquidaciones.

---

## 🏗️ Arquitectura del Sistema

El sistema fue desarrollado siguiendo estrictamente un **modelo de arquitectura en 3 capas**, garantizando la mantenibilidad, escalabilidad y separación de responsabilidades:

1. **Capa de Presentación (Frontend / Web)**:
   - Desarrollada en **Python Flask** utilizando plantillas Jinja2, HTML5, CSS3 personalizado (`style.css`) y JavaScript.
   - Interfaz moderna, responsiva, dinámica e intuitiva con Dashboard de control y paneles interactivos.

2. **Capa de Negocio (Backend)**:
   - Implementada en Python puro (`business/entities.py` y `business/controller.py`).
   - Contiene la lógica de dominio, validaciones de datos y reglas de negocio del sistema.

3. **Capa de Datos (Persistencia)**:
   - Base de datos relacional **SQLite3** gestionada a través de **SQLAlchemy ORM** (`datos/db.py`).
   - Manejo de persistencia, relaciones entidad-relación y consultas optimizadas.

---

## 👥 Modelo de Dominio y Entidades

- **Persona (Clase Base)**: Representa una entidad con datos personales (DNI/Pasaporte, Nombre, Apellido, Domicilio, Teléfono, Email, Contraseña encriptada).
  - **Agente**: Corredor o empleado de la inmobiliaria con legajo/matrícula y CUIL.
  - **Propietario**: Dueño titular de los inmuebles.
  - **Cliente**: Inquilino o comprador interesado.
- **Propiedad**: Inmueble administrado por la inmobiliaria (Dirección, Tipo [Alquiler/Venta], Zona, Estado [Disponible/Alquilada/Vendida] y Propietario asociado).
- **AgenteAsignado**: Registro histórico y activo que vincula a un Agente Inmobiliario con la gestión de una propiedad específica.
- **Contrato**: Acuerdo legal entre un Cliente, un Agente y una Propiedad. Incluye el monto de alquiler/venta, porcentaje de comisión inmobiliaria, estado (Solicitado, Activo, Finalizado) y fechas del acuerdo.
- **PagoInquilino**: Registro de cada canon locativo o pago mensual recibido por parte de los clientes para un período determinado.
- **PagoPropietario (Liquidación)**: Registro de la liquidación financiera realizada al propietario, detallando el monto bruto cobrado, la comisión retenida por la inmobiliaria y el monto neto transferido.

---

## ⚡ Funcionalidades Principales

### 1. 🔐 Autenticación y Seguridad
- **Inicio y Cierre de Sesión**: Acceso protegido exclusivo para Agentes Inmobiliarios.
- **Seguridad de Contraseñas**: Encriptación criptográfica de claves mediante *hashing* seguro (`werkzeug.security`).
- **Protección de Rutas**: Control de autorización mediante el decorador `@login_required` para prevenir accesos no autorizados.

### 2. 📊 Dashboard de Control y Estadísticas
- **Indicadores Generales (KPIs)**:
  - Total de propiedades registradas y desglose según su estado (Disponibles, Alquiladas, Vendidas).
  - Cantidad total de clientes y propietarios registrados.
  - Total de contratos activos.
- **Métricas Financieras del Período**:
  - Total recaudado en el mes (cobros de alquileres).
  - Total pendiente de cobro.
  - Comisiones netas ganadas por la inmobiliaria.
  - Pagos pendientes de transferir a propietarios.
  - **Índice de Eficiencia de Cobro (%)**.
  - Alerta de contratos con pagos atrasados.
- **Filtros Dinámicos**: Posibilidad de filtrar las estadísticas por Propietario específico, Cliente o Período mensual.

### 3. 🏠 Gestión de Propiedades (Inmuebles)
- **Registro de Propiedades**: Alta de nuevos inmuebles definiendo dirección, tipo de operación, zona y asignación de propietario.
- **Listado y Catálogo**: Vista centralizada de todas las propiedades con su estado actual y agente a cargo.
- **Detalle de Propiedad**: Información completa del inmueble, historial de agentes asignados y contratos asociados.
- **Asignación de Agentes**: Vinculación de agentes responsables a propiedades para seguimiento comercial.

### 4. 👨‍👩‍👧‍👦 Gestión de Clientes y Propietarios
- **Administración de Clientes**: Registro completo de datos personales y de contacto para inquilinos y compradores.
- **Administración de Propietarios**: Registro y catalogación de dueños de propiedades para la posterior liquidación de fondos.

### 5. 📑 Gestión de Contratos
- **Solicitud de Contrato**: Creación de un contrato asociando cliente, propiedad disponible y agente responsable.
- **Firma y Activación de Contrato**:
  - Al firmar el contrato, el sistema activa automáticamente la relación contractual.
  - Transición automática de estado: La propiedad pasa a estar **"alquilada"** o **"vendida"** según corresponda.
- **Configuración de Comisiones**: Definición del porcentaje de comisión aplicable a las operaciones.

### 6. 💰 Módulo de Finanzas y Liquidaciones
- **Registro de Pagos de Inquilinos**: Asignación de cobros mensuales por contrato y período correspondiente (Ej: `08/2026`).
- **Generación de Liquidaciones**: Proceso automático que calcula para cada cobro realizado:
  $$\text{Monto Neto a Propietario} = \text{Monto Cobrado} - \text{Comisión Inmobiliaria}$$
- **Gestión de Transferencias**: Control de liquidaciones con estado *Pendiente* y confirmación de transferencias realizadas al propietario (*Pagado*).
- **Resumen Financiero Centralizado**: Visualización global de la caja registradora, comisiones acumuladas y compromisos de pago.

---

## 📜 Reglas de Negocio Implementadas

1. **Disponibilidad para Contratación**: No se pueden crear solicitudes de contrato sobre propiedades que ya estén alquiladas, vendidas o fuera de servicio.
2. **Requisito de Agente Asignado**: Para iniciar un contrato sobre una propiedad, esta debe contar previamente con un agente inmobiliario asignado.
3. **Cambio Automático de Estado**: La firma de un contrato modifica automáticamente el estado de la propiedad a `alquilada` o `vendida`.
4. **Integridad Financiera**: No es posible registrar dos pagos para el mismo período (mes/año) sobre el mismo contrato.
5. **Cálculo Exacto de Liquidaciones**: Las liquidaciones a propietarios se derivan automáticamente de los cobros efectivos realizados a inquilinos, reteniendo el porcentaje exacto de comisión acordado en el contrato.

---

## 🚀 Cómo Ejecutar la Aplicación

1. **Asegurarse de tener Python 3.8+ instalado.**
2. **Navegar a la carpeta `TPI` e instalar dependencias (si aplica):**
   ```bash
   pip install -r requirements.txt
   ```
3. **Iniciar la aplicación:**
   ```bash
   python app.py
   ```
4. **Acceder desde el navegador web a:**
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

**Credenciales por defecto:**
- **Email:** `admin@inmogestion.com`
- **Contraseña:** `adminpassword`
