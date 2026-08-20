# InmoGestión - Sistema de Gestión Inmobiliaria

Este archivo contiene la información detallada del proyecto de acuerdo a las especificaciones del Trabajo Práctico Integrador (TPI).

---

## 📌 Descripción del Proyecto

**InmoGestión** es una plataforma web desarrollada para la gestión operativa, comercial y contable de una agencia inmobiliaria. El objetivo principal es optimizar la administración de inmuebles, clientes, propietarios y agentes, automatizando el flujo de trabajo desde la publicación de la propiedad hasta la firma del contrato y la liquidación mensual de alquileres con sus respectivas comisiones.

---

## 📐 Modelo de Dominio

- **Persona (Clase Base Abstracta)**
  - `Agente`: Empleado/corredor inmobiliario con matrícula y CUIL.
  - `Propietario`: Dueño titular del inmueble.
  - `Cliente`: Inquilino o comprador.
- **Propiedad**: Inmueble administrado (`direccion`, `tipo`, `zona`, `estado`, `id_propietario`).
- **AgenteAsignado**: Asociación entre Agente y Propiedad con registro temporal.
- **Contrato**: Acuerdo entre Cliente, Agente y Propiedad (`monto`, `comision_porcentaje`, `estado`, `fecha_contrato`).
- **PagoInquilino**: Registro del pago del canon locativo por parte del cliente.
- **PagoPropietario**: Liquidación del monto neto al propietario reteniendo la comisión de la inmobiliaria.

---

## 🏗️ Bosquejo de Arquitectura

El sistema utiliza un diseño en **3 Capas**:
1. **Capa de Presentación**: HTML5, CSS3, Jinja2 Templates y Flask Blueprints (`views/views.py`).
2. **Capa de Negocio**: Clases de dominio (`business/entities.py`) y controlador con lógica de negocio (`business/controller.py`).
3. **Capa de Datos**: Persistencia en base de datos **SQLite3** a través de **SQLAlchemy ORM** (`datos/db.py`).

---

## 📋 Requerimientos

### Funcionales

1. **Gestión de Usuarios y Seguridad**: Autenticación de Agentes Inmobiliarios mediante email y contraseña encriptada.
2. **Gestión de Propiedades**: Alta, consulta de catálogo, detalle y asignación de Agentes Inmobiliarios responsables.
3. **Gestión de Clientes y Propietarios**: Registro y administración de datos personales y de contacto.
4. **Gestión de Contratos**: Registro de solicitudes de contrato, firma/activación de contratos y actualización automática del estado de la propiedad (a `alquilada` o `vendida`).
5. **Administración Financiera y Cobros**: Registro de pagos mensuales de inquilinos.
6. **Liquidaciones a Propietarios**: Generación automática de liquidaciones descontando la comisión inmobiliaria y registro de transferencias efectuadas.
7. **Dashboard y Estadísticas**: Indicadores clave (KPIs), eficiencia de cobro, contratos atrasados y gráficos de resumen con filtros por cliente, propietario y período.

### No Funcionales

#### Portability
- **Web Multi-navegador**: Compatible con navegadores modernos (Chrome, Firefox, Edge, Safari).
- **Ejecución Única**: Ejecución mediante script principal `app.py`.

#### Security
- Contraseñas almacenadas con encriptación criptográfica (`werkzeug.security`).
- Variables de entorno y llaves secretas configurables vía `.env`.
- Rutas de aplicación protegidas mediante decoradores de autenticación (`@login_required`).

#### Maintainability
- Diseñado bajo la arquitectura en 3 capas.
- Control de versiones mediante GIT.
- Código en Python 3.8+ cumpliendo estándares de estilo (Flake8).

#### Reliability & Scalability
- Manejo independiente de sesiones de usuario (Cookies y Flask Sessions).
- Control de concurrencia y sesiones de base de datos a través de ORM.

#### Performance
- Funciona eficientemente en un equipo de cómputo estándar.

#### Flexibility
- Utiliza SQLite3 mediante SQLAlchemy ORM, permitiendo migrar a otros SGBD relacionales (PostgreSQL, MySQL).

---

## 🛠️ Stack Tecnológico

### Capa de Datos
- **Base de Datos**: SQLite3.
- **ORM**: SQLAlchemy.
- **Motivo**: Permite abstracción de datos, mapeo directo de objetos de dominio a tablas relacionales y portabilidad.

### Capa de Negocio
- **Lenguaje**: Python 3.8+.
- **Librerías**: `python-dotenv`, `datetime`, `functools`.
- **Motivo**: Alta legibilidad, agilidad en desarrollo y rica biblioteca estándar para manejo de reglas de dominio.

### Capa de Presentación
- **Framework**: Flask (Microframework Web).
- **Motor de Plantillas**: Jinja2.
- **Estilos**: CSS3 moderno con sistema de diseño responsive y diseño limpio.
- **Motivo**: Ligero, flexible y fácil integración con la capa de negocio de Python.