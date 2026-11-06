# Política releaseguard-v1

La aprobación requiere `tests`, `build`, `health`, `nonroot` y `scan` en `pass`. Un `fail` bloquea; cualquier ausencia, `not_run`, `error` o estado desconocido impide aprobar. No hay excepciones basadas en nombres de escenarios.

## Qué comprueba cada control

- **tests:** pytest ejecuta contratos HTTP, límites de entradas, invariantes de política, integridad y pruebas unitarias de las sondas. El resultado procede del código de salida y de JUnit. Las simulaciones de las pruebas unitarias no se presentan como ejecuciones Docker.
- **build:** construcción Docker real del target, con log e identidad inmutable de la imagen resultante.
- **health:** HTTP real contra `/health` dentro del contenedor, status 200 y JSON `{"status":"ok"}`, junto con el estado final del `HEALTHCHECK` de Docker. Un error de arranque o timeout se registra como error, no como el fallo HTTP esperado.
- **nonroot:** los cuatro UID de `/proc/1/status` (real, efectivo, guardado y filesystem) deben ser mayores que cero. Consultar solo `Config.User` sería insuficiente para demostrar las credenciales del proceso. Una lectura inválida es error, no fallo esperado.
- **scan:** Trivy sobre la imagen local ya construida, con inventarios OS y Python reconocidos (incluido FastAPI) y resultados JSON v2. Se usa `--image-src docker` para no escanear por error una etiqueta remota del mismo nombre.

## Vulnerabilidades

Trivy se ejecuta con `--scanners vuln --format json --exit-code 0`. El cero significa que ha completado el escaneo, **no que sea seguro**. El gate interpreta por separado los hallazgos del JSON y bloquea HIGH/CRITICAL, incluso sin versión corregida. Se conservan LOW/MEDIUM/UNKNOWN y sus versiones de corrección cuando Trivy las proporciona. No se inventan identificadores, métricas ni duraciones. No se filtran CVEs ni se silencia la salida del scanner.

Los errores de instalación o descarga de la base pueden impedir el análisis. La instalación tiene `continue-on-error` únicamente para permitir al runner generar un `not_run`; sus aserciones y el gate seguirán fallando. No hay un `continue-on-error` general que vuelva verde el laboratorio.

Un resultado sin HIGH/CRITICAL solo refleja las fuentes y reglas utilizadas en esa fecha. No cubre secretos, configuración de toda una infraestructura, malware, autorización de negocio ni vulnerabilidades desconocidas. La severidad UNKNOWN no bloquea en v1 y requiere revisión humana.

## Aprobación frente a demostración

Las expectativas son exactas: candidata = todo pasa; health-failure = solo health falla; root-user = solo nonroot falla. La aserción compara estados medidos con la expectativa **después** de calcular la decisión. Un fallo de escaneo o de pruebas adicional rompe la aserción, incluso en un caso intencionalmente defectuoso.

La imagen candidata puede ser elegible aunque el laboratorio detecte una avería distinta en un caso negativo. Esto no publica la API: la elegibilidad de la candidata depende de sus propios controles y el estado del laboratorio sigue siendo independiente y visible. Solo se exporta esa candidata, nunca los targets negativos.

## Límite de confianza de Actions

`pull_request` ejecuta código propuesto sin secretos, sin credenciales Git persistidas y con token de lectura en runners hospedados efímeros. No se despliegan sus artefactos. Una persona con permiso para cambiar `main` puede modificar los controles, por lo que la revisión y protección de rama son necesarias para una garantía organizativa; este portfolio no sustituye esas políticas.

El job privilegiado solo recibe un artefacto del build del mismo workflow en `main`. No descarga artefactos de PR de otras ejecuciones. La publicación de evidencia es independiente del gate de la aplicación. El frontend no dispone de tokens ni acciones remotas.

## Actualizar sin perder trazabilidad

1. Revisar la nueva release oficial de Python, dependencias o Trivy.
2. Modificar inputs `.in`, regenerar los locks con `pip-tools==7.6.2 --generate-hashes` sobre Python 3.13 y revisar diferencias. Mantener coherentes runtime y dev.
3. Actualizar digest base o checksum del binario Trivy cuando corresponda. Actualizar `docs/toolchain.json`.
4. Ejecutar pruebas y los tres escenarios; revisar JSON completo y artefactos.
5. Aprobar el cambio por evidencia. Nunca editar un informe para hacerlo pasar.
