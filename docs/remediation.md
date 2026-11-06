# Una candidata bloqueada de verdad

La [primera ejecución](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42256605849), commit `ff1bc8bded7a38c1b21cb2e57d4a45d9ff3a4fa7`, construyó los tres contenedores y detectó correctamente HTTP 503 y UID 0. La candidata pasó pruebas, construcción, salud y usuario, pero Trivy observó **47 hallazgos HIGH/CRITICAL**. Son hallazgos por paquete, no necesariamente 47 CVEs diferentes.

La imagen Python basada en Debian Bookworm contenía componentes del sistema con hallazgos sin parche indicado y paquetes de herramientas de instalación con versiones corregidas disponibles. La política bloqueó la candidata y las tres aserciones del laboratorio, porque el fallo de scan era adicional a los fallos esperados. No se generó un artefacto de imagen aprobada. El dashboard sí se construyó con los informes.

La corrección cambia a la base oficial Python Alpine, fijada por digest, y retira pip y las ruedas de ensurepip tras instalar las dependencias con hashes. La aplicación no necesita instaladores durante su ejecución. La selección de otra base reduce componentes y cambia el conjunto de dependencias del sistema; también cambia glibc por musl, por lo que debe comprobarse de nuevo la compatibilidad. No se borra el inventario del gestor de paquetes ni se omiten paquetes del scan. No se modifica ninguna severidad ni se añade una lista de exclusiones.

La base anterior está registrada en `docs/toolchain.json` y el commit inicial permite reproducirla. Los [artefactos originales](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42256605849/artifacts/13523411559) caducan a los 30 días. La evidencia también se conserva en [`evidence/initial-blocked.zip`](../evidence/initial-blocked.zip).

La corrección solo será efectiva cuando una nueva ejecución complete los cinco controles. El resultado real, sus herramientas y los nuevos hallazgos se conservan en el informe de esa ejecución. Un cambio de base no es una garantía de ausencia de vulnerabilidades.

## Resultado de la corrección

La [ejecución 42258176332](https://github.com/diegomarla11/ReleaseGuard/actions/runs/42258176332), commit `795d9b55aed5ab36f28249a22241830e2224fbbb`, verificó los tres casos: candidata aprobada y negativos bloqueados únicamente por salud o usuario. Trivy completó el escaneo del sistema y Python, sin hallazgos en esa ejecución. Se conservó únicamente la imagen candidata como artefacto aprobado. La evidencia completa está en `dashboard/public/reports/`, con su fecha, commit y metadatos de base.
