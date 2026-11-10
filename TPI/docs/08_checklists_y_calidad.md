# ✅ 8. Cumplimiento de Checklists Académicos y Calidad de Software

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 📋 1. Checklist sobre el Diseño en Capas (`checklist_capas.md`)

| Categoría | Requisito de la Cátedra | Estado | Evidencia de Cumplimiento en el Código |
| :--- | :--- | :---: | :--- |
| **General** | **Archivo raíz `app.py`** | ✅ Cumple | Existe `app.py` en la raíz del proyecto para inicializar la base, registrar blueprints y ejecutar el servidor web. |
| **General** | **Estructura de Carpetas Normalizadas** | ✅ Cumple | Carpetas bien definidas por capa: `views/` (Presentación), `business/` (Negocio), `datos/` (Datos). |
| **Presentación** | **No usa clases ni funciones de Datos** | ✅ Cumple | `views/views.py` tiene **cero imports** de `datos/db.py` ni de modelos de SQLAlchemy. Solo invoca funciones de `business/controller.py`. |
| **Presentación** | **Lógica en Negocio, no en vistas** | ✅ Cumple | Las rutas en `views.py` solo reciben inputs HTTP, los transforman en parámetros primitivos, llaman al controlador de negocio y renderizan la plantilla con los objetos recibidos. |
| **Presentación** | **Independiente de cambios en Datos** | ✅ Cumple | Modificaciones en los esquemas de tablas o nombres de columnas no afectan a las vistas, ya que estas solo interactúan con objetos de dominio. |
| **Negocio** | **No realiza llamadas directas a DB** | ✅ Cumple | `business/controller.py` no realiza consultas SQL ni instancia sesiones de base de datos; delega toda persistencia en `datos/db.py`. |
| **Negocio** | **Sin elementos de interfaz** | ✅ Cumple | `controller.py` no importa Flask, ni `render_template`, ni genera código HTML. Trabaja exclusivamente con lógica de dominio. |
| **Negocio** | **Independiente del motor de base de datos** | ✅ Cumple | El motor puede conmutar libremente entre SQLite3 y PostgreSQL sin modificar el código de la capa de negocio. |
| **Negocio** | **Devuelve Objetos de Negocio (BO)** | ✅ Cumple | Todas las funciones retornan instancias de clases de negocio (`Cliente`, `Propiedad`, `Contrato`, `Reclamo`, etc.) definidas en `business/entities.py`. |
| **Negocio** | **Valida reglas de negocio** | ✅ Cumple | Valida más de 14 reglas operativas formales (disponibilidad, inmutabilidad, cálculo de mora, cupos de visitas, no superposición horaria, etc.). |
| **Datos** | **Consultas centralizadas en la capa** | ✅ Cumple | Todas las sentencias y consultas de SQLAlchemy residen exclusivamente dentro de `datos/db.py`. |
| **Datos** | **Acceso exclusivo desde Negocio** | ✅ Cumple | Únicamente `business/controller.py` importa y hace uso de las funciones de `datos/db.py`. |
| **Datos** | **Uso de Base de Datos y ORM** | ✅ Cumple | Implementa persistencia relacional con SQLAlchemy ORM y base SQLite3 / PostgreSQL. |
| **Datos** | **Retorna Objetos de Negocio (BO)** | ✅ Cumple | Dispone de mappers dedicados (`to_bo_cliente`, `to_bo_propiedad`, `to_bo_contrato`, etc.) que transforman modelos ORM a clases de negocio. |

---

## 📋 2. Checklist sobre Buenas Prácticas en Python (`checklist_general.md`)

| Categoría | Requisito de la Cátedra | Estado | Evidencia de Cumplimiento en el Código |
| :--- | :--- | :---: | :--- |
| **General** | **Convención de Nombres Estándar** | ✅ Cumple | Clases en `PascalCase` (`Propiedad`, `PagoInquilino`), funciones y variables en `snake_case` (`calcular_mora`, `fecha_contrato`). |
| **General** | **Sin variables globales mutables** | ✅ Cumple | No se utilizan variables de estado globales en el código. Las configuraciones provienen del entorno (`.env`) o de parámetros de función. |
| **General** | **Cumplimiento de PEP 8 (Flake8)** | ✅ Cumple | Verificado mediante `flake8 .` con configuración `.flake8` estándar. |
| **General** | **Almacenamiento seguro de datos sensibles** | ✅ Cumple | Contraseñas protegidas mediante hash irreversible con salt (`werkzeug.security.generate_password_hash`). |
| **Web** | **Manejo de Errores HTTP Personalizados** | ✅ Cumple | Controladores y plantillas específicas para errores `403 Forbidden` (`templates/errors/403.html`) y `404 Not Found` (`templates/errors/404.html`). |
| **Web** | **Multiusuario y sesiones independientes** | ✅ Cumple | Manejo de sesiones de usuario mediante cookies cifradas independientes, permitiendo navegación simultánea desde diferentes sesiones o navegadores. |
| **Web** | **Diseño Responsive / Adaptive** | ✅ Cumple | Interfaz estilizada con CSS3 y media queries (`@media (max-width: 768px)`), completamente adaptable a dispositivos móviles y tablets. |
| **Opcional** | **Autorización y Roles (RBAC)** | ✅ Cumple | Implementación de decoradores `@login_required` y `@admin_required`, con perfiles `Administrador` y `Estándar`. |
| **Opcional** | **Tests Unitarios Automatizados (Pytest)** | ✅ Cumple | Suite completa de pruebas con fixtures en memoria en el directorio `tests/` validando reglas de negocio, integridad financiera y flujos web. |

