# Verificación de entrega

Fecha: 6 de noviembre de 2026. Este documento se actualizará con los resultados observados al terminar la entrega.

- Repositorio inicial local vacío; se conserva `.gitattributes` del primer commit remoto.
- Python 3.13 local: 29 pruebas de API, política, sondas e integridad superadas. Hay un aviso de deprecación de httpx en Starlette; no afecta al resultado, pero requiere futura migración del cliente de tests.
- Dashboard: TypeScript y build Vite ejecutados correctamente.
- Docker y Trivy locales no disponibles: se generó un informe real de intento incompleto. No se afirma haber ejecutado contenedores localmente.
- Revisión visual en navegador a 1440 × 1050 y 390 × 844: selección de escenarios, comparación, estados incompletos y bloqueados, detalle HTTP y versiones. Sin desbordamiento horizontal a 390 px. JSON servido y comparado byte a byte con su original.
- Primera ejecución Actions 42256605849: construcción y mediciones reales correctas; candidata bloqueada por 47 hallazgos HIGH/CRITICAL. Artefacto archivado y SHA-256 verificado. Corrección de base en curso; publicación pendiente de comprobación.

La API también se inició con Uvicorn en loopback y se verificaron `/health` y `/api/greet?name=Diego` mediante HTTP real. La sintaxis de Actions fue validada con actionlint 1.7.12.
