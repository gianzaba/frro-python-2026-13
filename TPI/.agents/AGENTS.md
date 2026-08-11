# Pautas y Reglas de Desarrollo para el TPI (UTN FRRO - Python)

Este archivo contiene las directrices técnicas, arquitectónicas y de calidad que deben cumplirse de manera estricta durante la solución y desarrollo del Trabajo Práctico Integrador (TPI).

---

## 1. Arquitectura en 3 Capas (Estricta)

La aplicación debe estructurarse en **Presentación**, **Negocio** y **Datos**. Las dependencias fluyen de arriba a abajo: `Presentación -> Negocio -> Datos`.

### A. Capa de Presentación (`views/` o `views.py`)
- **Prohibición absoluta:** NO importar ni llamar directamente a funciones, clases u objetos de la capa de Datos (`datos/db.py`).
- Toda interacción de usuario (botones, formularios, peticiones HTTP) debe delegarse a funciones de la **Capa de Negocio** (`business/controller.py`).
- Debe seguir funcionando sin cambios si se modifica el almacenamiento interno en la capa de datos.
- Archivo principal: `TPI/views/views.py` o dentro del módulo `views/`.

### B. Capa de Negocio (`business/` o `controller.py`)
- **Prohibición de consultas directas:** Ninguna función puede ejecutar SQL ni consultar bases de datos directamente. Debe hacerlo a través de la **Capa de Datos** (`datos/db.py`).
- **Separación de interfaz:** Ninguna función de negocio puede manejar HTML, respuestas Flask directas ni elementos de interfaz.
- **Formato de datos:** Las funciones deben retornar siempre **Objetos de Dominio/Entidades** (`business/entities.py` - Cliente, Propiedad, Contrato, etc.).
- **Reglas de negocio:** Se deben validar explícitamente las reglas de negocio y restricciones operativas en esta capa.
- Archivo principal: `TPI/business/controller.py` y `TPI/business/entities.py`.

### C. Capa de Datos (`datos/` o `db.py`)
- Es la única capa autorizada a realizar consultas a la base de datos (SQLite, MySQL, etc.).
- Las funciones deben retornar objetos/entidades de negocio.
- Solo la Capa de Negocio puede invocar funciones de la Capa de Datos.
- Archivo principal: `TPI/datos/db.py`.

---

## 2. Estándares de Código y Buenas Prácticas (Python & Web)

### Estilo de Código Python
- Cumplir strictly con **PEP 8** (verificación mediante `flake8`).
- **Convención de Nombres:** `snake_case` para variables y funciones, `PascalCase` para clases.
- **Variables Globales:** Prohibido el uso de variables globales.

### Seguridad
- Contraseñas almacenadas obligatoriamente con **encriptado criptográfico (hash con SHA-256 o bcrypt/pbkdf2)**.
- **Secretos:** Tokens, API Keys y credenciales en variables de entorno (`.env`), nunca harcodeados en el código.
- Manejo adecuado de autorización y respuestas de error HTTP (403, 404, 500).

### Multiusuario y Web
- Estado de sesión manejado mediante Cookies/Sessions/Tokens seguros.
- La aplicación debe funcionar correctamente e de forma independiente entre sesiones normales e incógnito.

---

## 3. Pruebas y Verificación

- Se debe mantener y ejecutar la suite de pruebas unitarias (`pytest`) en `TPI/tests/` para verificar reglas de negocio y flujo web.
- Cada cambio significativo debe pasar las validaciones antes de considerarse terminado.
