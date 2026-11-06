# Contrato de evidencia, esquema 1

`report.json` se genera mediante `python -m scripts.run_lab`. Sus valores proceden de la ejecución y del motor de política. El dashboard solo lo lee.

| Campo | Significado |
| --- | --- |
| `kind` | `laboratory_execution`: intento real de ejecución de ejemplos de laboratorio |
| `metadata.origin` | `local` o `github_actions` |
| `metadata.generated_at` | Momento UTC de comienzo de la recogida de evidencia, ISO 8601 |
| `metadata.commit`, `dirty` | HEAD disponible y presencia de modificaciones locales; commit nulo si aún no existe |
| `metadata.run_url` | URL real derivada de contexto Actions; nula en local |
| `metadata.tools` | Versiones observadas; nulo cuando la herramienta no está disponible |
| `policy` | Identificador, severidades bloqueantes y regla vigente |
| `scenarios[].checks` | Estado, explicación y medición cuando existe |
| `scenarios[].image_id` | ID de la imagen construida; nulo si no se construyó |
| `scenarios[].decision` | `approved`, `blocked`, `incomplete` |
| `scenarios[].assertion` | Comparación exacta con el fallo esperado y diferencias inesperadas |
| `application_decision` | Decisión de la candidata, no del caso seleccionado en pantalla |
| `laboratory_status` | Cumplimiento de las tres expectativas |
| `files` | Rutas relativas de evidencia y sumas SHA-256 |

Las versiones de Trivy incluyen la información de base que ofrece `trivy --version` al comienzo. Los JSON originales conservan `CreatedAt`, metadatos de imagen y cualquier dato de análisis que emita la herramienta. No se inventa una versión de base cuando Trivy no la devuelve. No se muestran porcentajes ni tiempos estimados; JUnit contiene las duraciones realmente medidas.

El directorio de salida debe ser nuevo: así no se confunde un JSON antiguo con un scan fallido reciente. `export_dashboard` valida decisiones, rutas y hashes antes de copiar exclusivamente `.json`, `.xml` y `.log`; excluye la imagen Docker. Los informes locales pueden incluir rutas del entorno de desarrollo y logs de herramientas: revísalos antes de compartirlos.

**Ejecución real** identifica cómo se obtuvo la evidencia; **ejemplo de laboratorio** identifica el propósito de las tres imágenes. Son conceptos compatibles. Esta entrega no incluye un conjunto ficticio de resultados de muestra. Los únicos datos sintéticos son fixtures internos de tests, nunca exportados como informes. Si se añadiera una vista previa de muestra, debería usar otro `kind`, una etiqueta persistente y no mezclarse con los resultados reales.

Los informes guardados en Git son una instantánea. CI los sustituye en el directorio de build con los de esa ejecución; no hace commits automáticos. Una recarga de la web no vuelve a ejecutar controles. Si el último workflow no llega a desplegar, se seguirá viendo la última instantánea publicada con su fecha original.
