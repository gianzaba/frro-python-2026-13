# 🚀 7. Guía de Puesta en Marcha y Despliegue

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 💻 Requisitos Previos del Sistema

- **Sistema Operativo:** Windows 10/11, Linux (Ubuntu, Debian, Fedora) o macOS.
- **Python:** Versión **3.10** o superior instalada en el sistema.
- **Gestor de Paquetes:** `pip` actualizado.
- **Navegador Web Moderno:** Google Chrome, Mozilla Firefox, Microsoft Edge o Safari.
- **(Opcional) Servidor PostgreSQL:** Solo en caso de desear persistencia en base de datos externa en lugar de SQLite local.

---

## 🛠️ Instalación y Configuración Paso a Paso

### 1. Ubicación del Proyecto
Abrir una terminal o consola de comandos y posicionarse en la carpeta raíz del TPI:
```bash
cd frro-python-2026-13/TPI
```

### 2. Creación y Activación del Entorno Virtual (Recomendado)
Es altamente aconsejable utilizar un entorno virtual aislado para evitar conflictos de librerías:

- **En Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(En caso de error de ejecución de scripts en PowerShell, ejecutar previamente: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **En Windows (CMD):**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```

- **En Linux / macOS (Bash / Zsh):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalación de Dependencias
Con el entorno virtual activado, instalar los paquetes listados en `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Incluye Flask, Werkzeug, SQLAlchemy, python-dotenv, ReportLab, pytest y flake8).*

### 4. Configuración de Variables de Entorno (`.env`)
Crear el archivo de configuración `.env` a partir de la plantilla provista `.env.example`:
- **En Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **En Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

**Parámetros configurables en `.env`:**
```ini
# Base de Datos (Omitir o dejar vacío para usar SQLite local automático)
# DATABASE_URL=postgresql://usuario:clave@localhost:5432/tpi_inmobiliaria

# Seguridad y Sesiones Web
SECRET_KEY=clave_secreta_super_segura_inmogestion_2026
FLASK_DEBUG=True
PORT=5000

# Parámetros Bancarios para Emisión de Boletas
INMO_BANCO=Banco de Santa Fe
INMO_TITULAR=InmoGestión S.R.L.
INMO_CUIT=30-71445566-8
INMO_CBU=0650020101100234567891
INMO_ALIAS=INMO.GESTION.B2B
```

---

## 🏁 Inicialización de Base de Datos y Poblado de Datos

El script principal [`app.py`](file:///app.py) ejecuta automáticamente en su arranque:
1. `init_db()`: crea todas las tablas relacionales y ejecuta migraciones si es necesario.
2. `seed_large_dataset()`: detecta si la base de datos es nueva o requiere datos iniciales y precarga automáticamente un ecosistema completo de prueba:
   - 5 Agentes comerciales (Administradores y Estándar).
   - 9 Propietarios y 11 Clientes.
   - 14 Inmuebles en diferentes zonas geográficas.
   - 12 Contratos con cláusulas legales completas.
   - 4 Reclamos estructurales con presupuestos y estados diversos.
   - 9 Pagos de inquilinos y liquidaciones a propietarios (con y sin mora).
   - 3 Agendas de visitas (con cupos libres y turnos completos).

---

## ▶️ Ejecución del Servidor Web

Para iniciar la aplicación, ejecutar:
```bash
python app.py
```

La consola indicará:
```text
Initializing database...
Starting Flask web server...
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Abrir cualquier navegador web y navegar a:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Credenciales de Acceso Precargadas

| Rol de Usuario | Correo Electrónico | Contraseña | Perfil y Alcance |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@inmogestion.com` | `adminpassword` | Acceso total, gestión de agentes, auditoría y liquidaciones. |
| **Administrador** | `valeria.torres@inmogestion.com` | `pass123` | Directora de agencia con permisos administrativos plenos. |
| **Agente Estándar** | `martin.gomez@inmogestion.com` | `pass123` | Corredor comercial (gestión de su propia cartera de inmuebles y clientes). |
| **Agente Estándar** | `lucas.benitez@inmogestion.com` | `pass123` | Corredor comercial. |
| **Agente Estándar** | `carolina.diaz@inmogestion.com` | `pass123` | Corredora comercial. |

---

## 🧪 Ejecución de Pruebas Automatizadas (Pytest)

El proyecto cuenta con una suite integral de **tests unitarios y de integración** que validan las reglas de negocio, los cálculos de mora, la inmutabilidad de contratos y los flujos web:

Ejecutar todos los tests:
```bash
pytest
```

Ejecutar tests con reporte detallado y visualización de pasos:
```bash
pytest -v
```

Ejecutar un módulo de test específico:
```bash
pytest tests/test_finance_rules.py -v
```

---

## 🔎 Verificación de Estilo y Calidad de Código (Flake8)

Para comprobar el cumplimiento estricto de las normas **PEP 8** exigidas por la cátedra:
```bash
flake8 .
```
*(El archivo `.flake8` configura la longitud máxima de línea y los directorios excluidos como `.venv` y `__pycache__`).*

