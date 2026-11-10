# 🛠️ 3. Tecnologías y Stack Técnico

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 🧰 Resumen General del Stack

| Componente | Tecnología Seleccionada | Versión | Justificación Técnica |
| :--- | :--- | :--- | :--- |
| **Lenguaje Core** | **Python** | 3.10+ | Lenguaje multiplataforma, expresivo y con tipado dinámico opcionalmente tipable. Estándar de la cátedra con soporte para programación orientada a objetos avanzada (herencia, propiedades, decoradores). |
| **Framework Web** | **Flask** | 3.1.x | Microframework web minimalista, liviano y altamente extensible. Provee Blueprints modulares, Context Processors y gestión de sesiones sin la sobrecarga ni el acoplamiento rígido de frameworks más pesados. |
| **Motor de Plantillas** | **Jinja2** | 3.1.x | Motor de templating declarativo, rápido y seguro. Permite herencia de layouts (`layout.html`), macros reutilizables y formateo dinámico con escape automático de caracteres para prevenir inyecciones XSS. |
| **Capa de Persistencia (ORM)** | **SQLAlchemy** | 2.0.x | ORM estándar de la industria Python. Brinda abstracción agnóstica del motor relacional, mapeo declarativo con herencia polimórfica (`polymorphic_on`), transaccionalidad robusta y prevención nativa de inyecciones SQL. |
| **Base de Datos Local** | **SQLite3** | Integrada | Motor relacional embebido que almacena la información en un archivo único (`tpi_inmobiliaria.db`). Ideal para desarrollo rápido, portabilidad sin dependencias de red y ejecución inmediata por parte de los docentes. |
| **Base de Datos Producción** | **PostgreSQL** (con `psycopg2`) | 14+ | Sistema gestor de bases de datos relacional robusto para entornos concurrentes de producción multiusuario. Soportado automáticamente cambiando la variable `DATABASE_URL`. |
| **Seguridad Criptográfica** | **Werkzeug Security** | 3.1.x | Funciones criptográficas `generate_password_hash` y `check_password_hash` empleando el algoritmo `pbkdf2:sha256` con salt aleatorio para evitar ataques por diccionario o rainbow tables. |
| **Generación de Documentos PDF** | **ReportLab** | 5.1.x | Biblioteca profesional para maquetado y generación programática de documentos PDF en memoria (boletas de alquiler con código de barras `Code128` y presupuestos técnicos de reparación). |
| **Gestión de Configuración** | **python-dotenv** | 1.2.x | Carga segura de variables de entorno desde el archivo `.env`, permitiendo desacoplar credenciales, claves secretas y datos SMTP del repositorio de código. |
| **Frontend & UI** | **HTML5 Semántico + CSS3 + Bootstrap Icons** | Nativo / CDN | Interfaz moderna basada en sistema Glassmorphism, paleta de contraste adaptable, diseño responsive *Mobile-First*, sin frameworks de JS pesados que dificulten la depuración. |
| **Suite de Pruebas** | **Pytest** | 9.x | Framework de pruebas automatizadas con fixtures, parametrización y aserciones directas para validar reglas de negocio, cálculos de mora y flujos web. |
| **Linter y Calidad de Código** | **Flake8** | 7.x | Herramienta de análisis estático de código que garantiza el cumplimiento estricto del estándar de estilo **PEP 8**, detectando variables no utilizadas, importaciones huérfanas y errores de formato. |

---

## 🔍 Análisis Detallado de Decisiones Técnicas

### 1. ¿Por qué Flask frente a Django?
Para el Trabajo Práctico Integrador, el objetivo principal radica en demostrar el dominio de la **Arquitectura en 3 Capas Desacopladas**. 
- Django acopla fuertemente los modelos ORM (`models.Model`) a los formularios (`forms.ModelForm`) y a las vistas genéricas, dificultando la separación pura entre Capa de Negocio y Capa de Datos.
- **Flask**, en cambio, es un microframework no prescriptivo. Permite estructurar la aplicación en módulos limpios, manteniendo la Capa de Negocio (`business/controller.py`) completamente agnóstica de la web y la Capa de Datos (`datos/db.py`) independiente de los controladores HTTP.

### 2. ¿Por qué SQLAlchemy ORM con Herencia Polimórfica?
En el dominio inmobiliario, el concepto de `Persona` se especializa en tres perfiles con comportamientos y atributos diferentes:
- `Agente`: Empleado de la firma con matrícula profesional, CUIL y rol administrativo.
- `Propietario`: Locador que posee inmuebles y percibe liquidaciones.
- `Cliente`: Locatario o comprador que solicita contratos y efectúa pagos.

Mediante SQLAlchemy se implementó el patrón **Single Table Inheritance** con extensión relacional:
```python
class PersonaTable(Base):
    __tablename__ = "persona"
    ...
    tipo_persona = Column(String(50), nullable=False)
    __mapper_args__ = {
        "polymorphic_on": tipo_persona,
        "polymorphic_identity": "persona",
    }

class AgenteTable(PersonaTable):
    __tablename__ = "agente"
    id = Column(Integer, ForeignKey("persona.id"), primary_key=True)
    cuil = Column(String(20), unique=True, nullable=False)
    matricula = Column(String(50), unique=True, nullable=False)
    rol = Column(String(50), default="Estándar", nullable=False)
    __mapper_args__ = {"polymorphic_identity": "agente"}
```
Esto simplifica el control de unicidad de emails y documentos a nivel de base de datos, evitando inconsistencias entre perfiles.

### 3. Soporte Dual de Bases de Datos con Fallback Automático
El sistema detecta automáticamente la presencia y disponibilidad de una base de datos PostgreSQL mediante la variable `DATABASE_URL` configurada en el `.env`. Si el servidor PostgreSQL no está disponible o la conexión falla (por ejemplo, al ejecutar el proyecto por primera vez en una máquina sin motor instalado), el sistema captura la excepción y conmuta de manera transparente al archivo local **SQLite3**:

```python
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{SQLITE_DB_PATH}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Warning: la base configurada falló ({e}). Usando SQLite local.")
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
```
Esto garantiza **portabilidad absoluta** (ejecución "plug and play" en la corrección docente).

### 4. Generación Dinámica de PDFs con ReportLab
Para emitir documentos contables y técnicos formales, se descartó el uso de herramientas pesadas basadas en navegadores sin cabeza (como WeasyPrint o wkhtmltopdf que requieren binarios del sistema operativo) y se integró **ReportLab**:
- Permite construir en memoria (`io.BytesIO`) documentos vectoriales livianos.
- Genera códigos de barras estándar **Code128** para la individualización y conciliación unívoca de comprobantes de pago.
- No requiere dependencias externas en el sistema operativo del cliente ni del servidor.

