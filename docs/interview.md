# Cómo defender ReleaseGuard en una entrevista

## Explicación en 45 segundos

«Soy Diego, graduado en Ingeniería Informática. ReleaseGuard es un proyecto personal para practicar cómo convertir condiciones de publicación en controles automáticos. Una API mínima pasa pruebas, se construye con Docker y se comprueba su salud, el usuario real del proceso y sus vulnerabilidades con Trivy. Introduzco dos defectos controlados para demostrar que el pipeline los detecta. El dashboard estático permite ver qué pasó y descargar la evidencia. No hay una API productiva ni infraestructura cloud desplegada: lo que publico es el informe del laboratorio.»

Antes de decir «lo detecta», abre la ejecución actual: si Docker o Trivy no llegaron a ejecutarse, explica que el diseño y los tests están preparados, pero esa verificación sigue pendiente. No sustituyas evidencia por la expectativa del escenario.

## Decisiones y sus motivos

- **FastAPI mínima:** el objeto del proyecto es el proceso de entrega, no construir un producto de negocio. El endpoint funcional y `/health` permiten observar comportamiento real.
- **React estático:** hace accesible la evidencia sin mantener backend, credenciales ni contenedores públicos. Cambiar de escenario solo selecciona un informe.
- **Usuario 10001:** reduce privilegios. Medir PID 1 demuestra el estado del proceso, no solo una instrucción declarativa. No elimina por sí solo el riesgo de escape del contenedor.
- **Digest y locks:** mantienen estables la base y las dependencias; las actualizaciones son cambios revisables. Esto exige mantenimiento, porque fijar una versión no la hace segura para siempre.
- **HIGH/CRITICAL con o sin parche:** regla inicial sencilla y conservadora. No se puede garantizar que la candidata siga pasando mañana; la base de vulnerabilidades evoluciona.
- **Fail closed:** «no tengo resultado» y «pasa» son estados distintos. Un scanner caído no autoriza una entrega.
- **Fallo esperado exacto:** el laboratorio solo pasa cuando falla el control previsto y pasan los demás. De otro modo, un error de infraestructura podría confundirse con una demostración correcta.
- **Dos decisiones:** la API puede quedar bloqueada mientras la evidencia se publica. La aserción del caso negativo mide si el control funcionó, no si esa imagen es apta.
- **Permisos por job:** los PR no usan secretos ni permisos de publicación; el job privilegiado solo despliega archivos estáticos de `main`.
- **Sin Kubernetes/Terraform:** no resuelven una necesidad del MVP. Añadirlos ahora dificultaría explicar y verificar el comportamiento básico.

## Demostración sugerida

1. Abrir la candidata, leer su fecha y decisión real.
2. Seleccionar fallo de salud y abrir el detalle HTTP y `docker-health.json`.
3. Seleccionar usuario privilegiado y enseñar los UID medidos.
4. Comparar antes/después sin confundir el cambio de código con una nueva ejecución.
5. Abrir Trivy JSON y el workflow correspondiente. Si no existe scan, enseñar «No ejecutado» y explicar por qué no es verde.

## Cinco preguntas de práctica

1. ¿Por qué un escaneo no ejecutado impide aprobar la candidata?
2. ¿Cómo demuestras que el contenedor corre sin privilegios, más allá del Dockerfile?
3. ¿Cómo puede el laboratorio pasar cuando una de sus imágenes está bloqueada?
4. ¿Qué evita que un pull request publique la demo con permisos privilegiados?
5. ¿Qué demuestra Trivy y qué riesgos no puede descartar?
