# Verificación de entrega

Fecha: **6 de noviembre de 2026**, zona de presentación Europe/Madrid.

## Ejecución reproducible verificada

[Ejecución 42258176332](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42258176332), código en commit **`795d9b55aed5ab36f28249a22241830e2224fbbb`**. Inicio registrado: 17:04:46 UTC (18:04:46 Madrid).

| Caso | Tests | Build | Salud | UID PID 1 | Trivy | Decisión | Aserción del laboratorio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Candidata | 29 pasan | Pasa | HTTP 200 / healthy | 10001 | Pasa | Aprobada | Pasa |
| Fallo de salud | 29 pasan | Pasa | HTTP 503 / unhealthy | 10001 | Pasa | Bloqueada | Pasa |
| Usuario privilegiado | 29 pasan | Pasa | HTTP 200 / healthy | 0 | Pasa | Bloqueada | Pasa |

Trivy 0.76.2 informó cero hallazgos en los cinco niveles de severidad en esta ejecución. Esto describe ese análisis y su base, no demuestra ausencia total o futura de vulnerabilidades. El informe conserva la versión de la base y sus fechas de actualización y descarga.

Herramientas observadas: Python 3.13.18, FastAPI 0.162.0, Uvicorn 0.54.0, pytest 9.2.0 y Docker Engine 28.0.4. El informe JSON contiene la información completa. Las 29 pruebas se ejecutaron sin errores, fallos ni skips.

- [Evidencia original de Actions](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42258176332/artifacts/13522804549), ZIP SHA-256: `7c1f87b4c5883d5501a8a4a26560ccbf579eab8c3f5853d46efaa2a190965020`. Descargado y comprobado antes de copiarlo a `dashboard/public/reports/`.
- [Imagen candidata aprobada](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42258176332/artifacts/13523592224). No se exportaron las imágenes defectuosas.
- [Remediación del bloqueo inicial](remediation.md): se conserva el ZIP original en Git, con SHA-256 `5f8806af5983b94517028a9944e1537ba2b9342ea3ea6df062891c233f4f59f5`.

## Verificación local e interfaz

- Repositorio local originalmente vacío; se preservó `.gitattributes` del primer commit remoto. AccessLens no se modificó.
- 29 pruebas locales superadas en Python 3.13.13. Existe un aviso de deprecación de httpx en Starlette: el cliente de tests funciona y necesitará una migración futura.
- API iniciada con Uvicorn en loopback: `/health` y `/api/greet?name=Diego` respondieron correctamente mediante HTTP real.
- TypeScript y build Vite correctos; `npm ci` también se ejecutó en Actions.
- Workflow validado con actionlint 1.7.12.
- Revisión visual en navegador: escritorio de 1440 px y móvil de 390 × 844. Selección de escenarios, comparación, estados incompletos, bloqueados y aprobados, medición HTTP y versiones comprobados. Sin desbordamiento horizontal de la página a 390 px; las tablas tienen scroll propio.
- JSON servido localmente y comparado byte a byte con el original. Capturas locales en `evidence/desktop.jpg` y `evidence/mobile.jpg`, excluidas de Git para no confundirlas con mediciones del pipeline.
- Docker y Trivy no están disponibles en este Mac. Los contenedores y scans de esta entrega **sí se ejecutaron en GitHub Actions**. Instalar ambas herramientas sigue siendo necesario para repetir el laboratorio completo en local.

## Publicación

[Demo publicada](https://diegomarla11.github.io/ReleaseGuard/) verificada por HTTP y en navegador: candidata aprobada, negativos bloqueados e informe del commit `795d9b55aed5ab36f28249a22241830e2224fbbb`. Los cuatro jobs de la ejecución 42258176332 terminaron en success. El JSON público coincide byte a byte con el artefacto descargado y las 31 evidencias originales publicadas coinciden con sus SHA-256.

No se publicó una API: Pages sirve exclusivamente el dashboard y los informes estáticos. La publicación quedó habilitada por el propietario en Settings → Pages → GitHub Actions. Las protecciones adicionales de rama y environment están recomendadas en el README, pero su configuración no fue verificada ni se afirma que estén activas.

La instantánea se conserva en Git sin modificar sus datos ni su commit de origen. Un commit de documentación y archivo de evidencia puede ser posterior al commit analizado, sin implicar una nueva ejecución. Los enlaces y fechas del informe son la autoridad para saber qué código se comprobó.
