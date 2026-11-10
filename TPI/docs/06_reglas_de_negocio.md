# 📜 6. Matriz de Reglas de Negocio y Restricciones Operativas

**InmoGestión B2B - Sistema Integral de Gestión Inmobiliaria**  
*Cátedra: Soporte a la Gestión con Tecnologías de la Información / Python*  
*Universidad Tecnológica Nacional - Facultad Regional Rosario (UTN FRRO)*

---

## 🛡️ Matriz General de Reglas de Negocio

El sistema implementa y valida de forma estricta las siguientes reglas operativas en la **Capa de Negocio** (`business/controller.py`) y a nivel de restricciones en la **Capa de Datos** (`datos/db.py`):

| Código | Regla de Negocio | Capa Validadora | Comportamiento y Restricción | Test Automatizado Asociado |
| :---: | :--- | :---: | :--- | :--- |
| **RN-01** | **Disponibilidad para Contratos** | Negocio (`controller.py`) | Solo se puede solicitar o firmar un contrato sobre propiedades en estado `disponible`. Se rechaza la solicitud si está `alquilada` o `vendida`. | `test_business_rules.py::test_rn01` |
| **RN-02** | **Asignación Agente-Contrato** | Negocio (`controller.py`) | El agente que suscribe el contrato debe ser el comercial que posee la asignación activa sobre la propiedad a comercializar. | `test_business_rules.py::test_rn02` |
| **RN-03** | **Multi-propiedad por Agente** | Negocio (`controller.py`) | Un agente comercial puede tener asignadas múltiples propiedades simultáneamente sin restricciones ni topes artificiales. | `test_business_rules.py::test_rn03` |
| **RN-04** | **Inmutabilidad Contractual** | Negocio (`controller.py`) | Una vez firmado el contrato (`estado == 'activo'`), queda estrictamente prohibido agregar, editar o suprimir cláusulas, o alterar honorarios. | `test_clausulas_y_comision.py::test_inmutabilidad` |
| **RN-05** | **Control Estricto de Cupos en Visitas** | Negocio (`controller.py`) | No se permite inscribir personas a un turno de visita cuya cantidad de inscriptos sea igual o superior a su `cupo_maximo`. El turno pasa a `completo`. | `test_business_rules.py::test_cupo_visita` |
| **RN-06** | **No Superposición Horaria de Visitas** | Negocio (`controller.py`) | Un agente comercial no puede tener dos turnos de visita agendados cuyos rangos horarios se solapen entre sí. | `test_business_rules.py::test_superposicion` |
| **RN-07** | **Visitas solo en Inmuebles Disponibles** | Negocio (`controller.py`) | Solo se pueden planificar agendas de visita en propiedades con estado `disponible`. | `test_business_rules.py::test_visita_disponible` |
| **RN-08** | **Reclamos sobre Contratos Activos** | Negocio (`controller.py`) | Solo se pueden asentar reclamos e incidencias estructurales sobre contratos en estado `activo`. | `test_reclamos_y_agentes.py::test_reclamo_activo` |
| **RN-09** | **Cálculo Automático de Mora Diaria (0.2%)**| Negocio (`controller.py`) | Todo pago de alquiler efectuado después del día 10 devenga mora automática del 0.2% diario por cada jornada de retraso. | `test_finance_rules.py::test_mora_calculo` |
| **RN-10** | **Unicidad de Pago Mensual por Contrato** | Negocio (`controller.py`) | No se puede registrar más de un pago de alquiler para el mismo contrato y mismo período (`YYYY-MM`). | `test_finance_rules.py::test_doble_pago` |
| **RN-11** | **Liquidación Condicionada al Cobro** | Negocio (`controller.py`) | No se puede generar la liquidación a un propietario si el inquilino no ha cancelado previamente el canon del período correspondiente. | `test_finance_rules.py::test_liquidacion_previa` |
| **RN-12** | **Control de Acceso y Roles (RBAC)** | Presentación y Negocio | La generación masiva de liquidaciones, transferencias a propietarios, exportación CSV y gestión de agentes requieren rol `Administrador`. | `test_agentes_acceso_datos.py::test_roles` |
| **RN-13** | **Cifrado Criptográfico Obligatorio** | Negocio (`controller.py`) | Las contraseñas de todos los agentes se almacenan obligatoriamente hasheadas con algoritmo criptográfico seguro (`pbkdf2:sha256`). | `test_agentes_acceso_datos.py::test_hash` |
| **RN-14** | **Unicidad de Identificadores en DB** | Datos (`datos/db.py`) | Email, DNI/Documento, CUIL y Matrícula Profesional deben ser únicos e irrepetibles a nivel de constraints de base de datos. | `test_agentes_acceso_datos.py::test_unicidad` |
| **RN-15** | **Control Anti-Spam en Alertas de Mora** | Negocio (`controller.py`) | Si el contrato ya registró un aviso de mora en el día de la fecha (`fecha_ultimo_aviso_mora == date.today()`), se omite el reenvío. | `test_notificaciones_email.py::test_antispam` |
| **RN-16** | **Aislamiento de Cartera Comercial** | Negocio (`controller.py`) | Cada agente comercial estándar solo visualiza y administra sus propios clientes y propietarios registrados. | `test_cartera_y_cancelacion_contratos.py::test_cartera` |
| **RN-17** | **Cancelación Concurrente de Solicitudes** | Negocio (`controller.py`) | Al firmar un contrato sobre una propiedad, cualquier otra solicitud pendiente en borrador sobre ese inmueble pasa automáticamente a `cancelado`. | `test_cartera_y_cancelacion_contratos.py::test_cancelacion` |
| **RN-18** | **Traspaso de Titularidad tras Venta** | Negocio (`controller.py`) | Cuando un inmueble vendido vuelve a administrarse, se transfiere la titularidad al comprador, archivando el contrato anterior y liberando la propiedad. | `test_nuevas_funcionalidades.py::test_traspaso` |

