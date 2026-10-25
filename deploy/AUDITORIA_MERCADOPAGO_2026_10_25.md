# Auditoría de colaboraciones con Mercado Pago

Fecha: 25 de octubre de 2026, Ciudad de México.

## Seguimiento: correcciones autorizadas y publicadas

Después de esta auditoría, el propietario autorizó implementar y desplegar las
correcciones sin cobros reales ni reclasificación masiva de históricos. Las
59 pruebas iniciales ya pasan. La validación ampliada suma 207 pruebas de la
aplicación en PostgreSQL y 47 del panel en SQLite, todas satisfactorias, además
del recorrido de navegador con proveedor simulado. Se aplicó la migración aditiva
y se reiniciaron ambos servicios. Los 25 registros históricos permanecen intactos.

La validación con cuentas reales del sandbox sigue pendiente; no se ejecutaron
cobros ni devoluciones reales. Detalles y límites en
[MERCADOPAGO_OPERACION.md](MERCADOPAGO_OPERACION.md).

## Resultado de la auditoría previa a las correcciones

El resto de este documento conserva los hallazgos y la matriz de la fase previa;
sus fallos y las referencias a la falta de autorización describen ese momento,
no el estado publicado después de la autorización.


**La integración todavía no supera la validación de confiabilidad.** Se ejecutaron
59 pruebas distintas (54 nuevas y cinco existentes) contra SQLite temporal y
PostgreSQL temporal: **24 pasan y 35 fallan en ambos motores**. Son 35 pruebas
fallidas, no 35 vulnerabilidades independientes; varios casos comprueban facetas
del mismo problema. Las bases PostgreSQL de auditoría se eliminaron al finalizar.

Las operaciones del proveedor se simularon en todos los tests. En producción solo
se realizaron consultas GET de lectura y un POST de diagnóstico con firma
intencionalmente inválida que se rechazó antes de consultar pagos. No se crearon
cobros, capturas, reembolsos, transferencias ni nuevas preferencias reales. No se
cambiaron estados de los donativos existentes ni se reiniciaron servicios.

## Comprobación real, de solo lectura

- Credencial de producción configurada y API de cuenta: HTTP 200, cuenta de México.
- Se consultó el único donativo local marcado como aprobado. La API respondió
  HTTP 200 y confirmó `approved`, monto local coincidente, MXN, receptor de la
  cuenta autenticada, referencia local correspondiente y modo de producción.
- Hay 25 registros locales: uno aprobado y 24 pendientes. De los pendientes,
  diez carecen de preferencia. Un registro pendiente no demuestra que exista un
  cargo ni dinero en tránsito; parte de ese grupo puede ser un intento fallido.
- `/donar/` responde HTTP 200. El webhook público sin cookie CSRF responde
  HTTP 403 antes de llegar a la validación HMAC. La prueba local de una
  notificación correctamente firmada y sin cookie reproduce el mismo bloqueo.

No se validaron con datos de producción todos los pendientes, ni se realizaron
compras con cuentas de prueba de Mercado Pago. Eso requiere una fase posterior
controlada en sandbox. La prueba de lectura de un pago real no sustituye esa fase.

## Hallazgos y orden de atención

| Prioridad | Hallazgo reproducido | Consecuencia | Corrección propuesta |
|---|---|---|---|
| Crítica | El webhook sigue sujeto a CSRF de navegador | Las notificaciones servidor a servidor pueden recibir 403 y no actualizar el donativo | Eximir solo ese endpoint de CSRF y conservar autenticación HMAC obligatoria; mantener CSRF en el checkout público |
| Alta | Los errores de JSON, SDK y API terminan en HTTP 200 | El proveedor puede considerar atendido un evento no conciliado | Diferenciar entrada inválida, firma inválida y error temporal; devolver estado reintentable al fallar la conciliación |
| Alta | El retorno `/exito/` muestra agradecimiento sin comprobar un pago | Se puede presentar un éxito aunque la base siga pendiente | Mostrar únicamente el estado persistido y validado, con referencia de retorno no falsificable; no fiarse de parámetros `status` |
| Alta | La deduplicación ignora toda actualización del mismo pago ya aprobado | Un reembolso posterior no cambia el estado; el saldo y los colaboradores pueden quedar incorrectos | Procesar cambios posteriores con idempotencia por versión/fecha; contemplar reembolsos, parciales, cancelaciones, revisión y contracargos |
| Alta | Faltan verificaciones explícitas de monto, moneda, ID, receptor y entorno | Respuestas inconsistentes pueden marcar aprobaciones | Comparar el recurso autorizado consultado con la donación, preferencia y cuenta esperadas antes de guardar |
| Alta | No se protege el orden de actualización ni se bloquea el registro | Un estado antiguo puede reemplazar otro posterior, o un intento rechazado reemplazar un pago aprobado diferente | Conciliación transaccional, bloqueo de fila y control de fecha e identidad del pago |
| Media | Reenviar el mismo formulario crea dos checkouts | Aparecen intentos duplicados; esto no prueba dos cargos reales | Identificador estable por solicitud, reutilización de preferencia e idempotencia antes del llamado externo |
| Media | Se aceptan fracciones de centavo | La base puede redondear un monto distinto al enviado al proveedor | Rechazar importes no finitos, fuera de rango o con más de dos decimales antes de invocar el SDK |
| Media | No se distinguen fallos de creación y pagos en espera | Los errores de preferencia quedan como pendientes de pago | Estado operativo específico para el fallo de checkout, conservando la referencia si el resultado remoto es incierto |
| Media | Se cuentan colaboradores por correo sin normalizar | Los anónimos vacíos se agrupan como uno y diferencias de mayúsculas duplican personas | Identidad normalizada y criterio explícito para donantes sin correo; mantener separada la base fija de 40 |
| Media | Se registra el cuerpo completo de la notificación | Se almacenan campos enviados innecesarios en logs | Guardar únicamente los identificadores y resultados necesarios; minimizar también el resumen persistido del pago |
| Media | La vista pendiente promete un correo que no se envía | El usuario espera una comunicación inexistente | Retirar la promesa o implementar el envío autorizado y probado |
| Media | Falta validación defensiva de la URL de checkout | Una respuesta errónea puede redirigir fuera de Mercado Pago o a HTTP | Validar HTTPS y el dominio esperado del proveedor antes de redirigir |
| Media | Se invoca el SDK sin configuración suficiente y con sus límites predeterminados | Intentos fallidos y esperas extensas | Validación previa de credenciales, secreto y entorno; timeout y reintentos acotados |

Las pruebas de monto, receptor o entorno manipulan respuestas simuladas. Demuestran
la ausencia de comprobaciones locales, no que un tercero pueda controlar por sí
solo una respuesta de la API autenticada. La credencial real y el pago consultado
sí resultaron coherentes.

## Fuentes oficiales contrastadas

- [Webhooks de Checkout Pro mediante Preferences](https://www.mercadopago.com.mx/developers/es/docs/checkout-pro-preferences/additional-content/notifications/webhooks): firma HMAC, parámetros y consulta del recurso; respuestas y reintentos de entrega.
- [Crear preferencia](https://www.mercadopago.com.mx/developers/es/reference/online-payments/checkout-pro-preferences/create-preference/post): flujo actual basado en `/checkout/preferences`.
- [Estados de pagos](https://www.mercadopago.com.mx/developers/es/docs/checkout-api-payments/response-handling/query-results?scope=prod): estados, contracargos y reembolsos parciales.
- [Credenciales](https://www.mercadopago.com.mx/developers/es/docs/subscriptions/resources/credentials-best-practices/secure-credentials): uso del token en encabezados; no se imprimieron las credenciales.

No se propone migrar la integración a Orders como parte de esta auditoría. El
checkout existente utiliza Preferences y debe probarse conforme a ese producto.

## Artefactos y reproducción

Pruebas nuevas: `donaciones/test_mercadopago.py`. Están diseñadas para expresar el
comportamiento esperado y reproducir los fallos de la fase inicial. En esa fase
no constituían una suite verde; tras las correcciones autorizadas, sí pasan. Las llamadas al SDK están reemplazadas por mocks y los
casos nuevos usan credenciales ficticias.

```bash
DEBUG=False DJANGO_SETTINGS_MODULE=panel.public_test_settings venv/bin/python manage.py test donaciones --noinput
```

También se ejecutaron contra una base PostgreSQL de nombre aleatorio
`test_nexocontable_mp_audit_*`, distinta de la base productiva y eliminada tras
cada corrida. Se creó el esquema actual sin semillas históricas del SAT, porque
esta auditoría evalúa el flujo de pagos y no las migraciones de catálogos.

Registros locales de la ejecución:

- `/tmp/mercadopago-auditoria-postgres.log`
- `/tmp/mercadopago-auditoria-sqlite.log`

## Estado de las correcciones

**No se aplicaron correcciones al flujo financiero.** La revisión automática
rechazó el intento de implementar cambios en conciliación, estados, checkout,
modelos y migraciones porque la solicitud original autorizaba probar, y esos
cambios requieren autorización explícita. El código nuevo de servicio propuesto
no se creó y el modelo financiero original permanece sin modificaciones.

Antes de publicar correcciones se requiere autorización para implementar y probar
los cambios descritos, aplicar las migraciones que resulten necesarias y reiniciar
los servicios. La intervención no debe capturar, devolver ni alterar dinero, ni
reclasificar pagos históricos de producción sin una conciliación autorizada aparte.

La siguiente fase debe cubrir: tests actuales en verde, regresiones de aplicación
y panel, comportamiento transaccional en PostgreSQL y pruebas sandbox con cuenta
compradora/vendedora y webhooks del proveedor. No solicitar credenciales por chat.

## Matriz de pruebas

| Clase | Caso | Resultado |
|---|---|---|
| `DonacionesWebhookTests` | `test_webhook_rechaza_firma_invalida` | PASA |
| `DonacionesWebhookTests` | `test_webhook_aprueba_donativo_con_firma_valida` | PASA |
| `DonacionesPublicasTests` | `test_colaboradores_incluye_base_sin_donativos` | PASA |
| `DonacionesPublicasTests` | `test_base_se_suma_a_colaboradores_confirmados_sin_duplicar_correo` | PASA |
| `DonacionesPublicasTests` | `test_privacidad_disponible_y_plegada_al_abrir` | PASA |
| `MercadoPagoRobustezTests` | `test_webhook_firmado_no_necesita_cookie_csrf` | FALLA |
| `MercadoPagoRobustezTests` | `test_reembolso_posterior_a_aprobacion_no_se_ignora` | FALLA |
| `MercadoPagoRobustezTests` | `test_monto_incorrecto_no_aprueba` | FALLA |
| `MercadoPagoRobustezTests` | `test_error_del_proveedor_devuelve_error_reintentable` | FALLA |
| `MercadoPagoRobustezTests` | `test_no_se_acepta_webhook_sin_secreto_ni_en_debug` | FALLA |
| `MercadoPagoRobustezTests` | `test_retorno_manipulado_no_afirma_un_pago_aprobado` | FALLA |
| `MercadoPagoRobustezTests` | `test_monto_con_fraccion_de_centavo_no_inicia_checkout` | FALLA |
| `MercadoPagoRobustezTests` | `test_anonimos_distintos_no_se_colapsan_en_un_solo_colaborador` | FALLA |
| `MercadoPagoRobustezTests` | `test_firma_incorrecta_no_consulta_api` | PASA |
| `MercadoPagoRobustezTests` | `test_firma_ausente_no_consulta_api` | PASA |
| `MercadoPagoRobustezTests` | `test_webhook_solo_admite_post` | PASA |
| `MercadoPagoRobustezTests` | `test_json_invalido_se_rechaza` | FALLA |
| `MercadoPagoRobustezTests` | `test_json_array_se_rechaza` | FALLA |
| `MercadoPagoRobustezTests` | `test_data_de_tipo_incorrecto_se_rechaza` | FALLA |
| `MercadoPagoRobustezTests` | `test_otro_tipo_de_evento_no_modifica_donativos` | PASA |
| `MercadoPagoRobustezTests` | `test_id_diferente_en_query_y_cuerpo_no_se_procesa` | FALLA |
| `MercadoPagoRobustezTests` | `test_moneda_incorrecta_no_aprueba` | FALLA |
| `MercadoPagoRobustezTests` | `test_receptor_incorrecto_no_aprueba` | FALLA |
| `MercadoPagoRobustezTests` | `test_pago_de_prueba_no_cuenta_como_produccion` | FALLA |
| `MercadoPagoRobustezTests` | `test_id_de_api_diferente_no_aprueba` | FALLA |
| `MercadoPagoRobustezTests` | `test_referencia_de_otro_donativo_no_existe_se_ignora` | PASA |
| `MercadoPagoRobustezTests` | `test_api_sin_referencia_no_aprueba` | PASA |
| `MercadoPagoRobustezTests` | `test_api_sin_estado_no_aprueba_ni_asigna_pago` | FALLA |
| `MercadoPagoRobustezTests` | `test_timeout_del_proveedor_permite_reintento` | FALLA |
| `MercadoPagoRobustezTests` | `test_rechazo_se_registra` | PASA |
| `MercadoPagoRobustezTests` | `test_cancelacion_se_registra` | FALLA |
| `MercadoPagoRobustezTests` | `test_contracargo_reemplaza_aprobacion` | FALLA |
| `MercadoPagoRobustezTests` | `test_parcial_no_reporta_total_integro_como_confirmado` | FALLA |
| `MercadoPagoRobustezTests` | `test_notificaciones_duplicadas_no_crean_otro_donativo` | PASA |
| `MercadoPagoRobustezTests` | `test_estado_antiguo_no_reemplaza_un_estado_mas_reciente` | FALLA |
| `MercadoPagoRobustezTests` | `test_otros_intentos_rechazados_no_quitan_aprobacion_confirmada` | FALLA |
| `MercadoPagoRobustezTests` | `test_no_se_registra_el_cuerpo_privado_del_webhook_en_logs` | FALLA |
| `MercadoPagoRobustezTests` | `test_pendiente_no_promete_un_correo_que_no_se_envia` | FALLA |
| `MercadoPagoRobustezTests` | `test_usuario_ajeno_no_ve_un_exito_solo_por_id_en_la_url` | FALLA |
| `MercadoPagoRobustezTests` | `test_donativos_rechazados_y_reembolsados_no_incrementan_colaboradores` | PASA |
| `MercadoPagoRobustezTests` | `test_correos_repetidos_con_distinta_capitalizacion_son_un_colaborador` | FALLA |
| `MercadoPagoCheckoutTests` | `test_checkout_anonimo_crea_pendiente_y_referencia` | PASA |
| `MercadoPagoCheckoutTests` | `test_monto_personalizado_tiene_prioridad` | PASA |
| `MercadoPagoCheckoutTests` | `test_limites_10_y_100000_son_aceptados` | PASA |
| `MercadoPagoCheckoutTests` | `test_montos_invalidos_no_llaman_al_proveedor` | PASA |
| `MercadoPagoCheckoutTests` | `test_montos_de_mas_de_dos_decimales_se_rechazan` | FALLA |
| `MercadoPagoCheckoutTests` | `test_csrf_sigue_obligatorio_para_crear_checkout` | PASA |
| `MercadoPagoCheckoutTests` | `test_error_api_no_redirige_a_checkout_ni_confirma_pago` | PASA |
| `MercadoPagoCheckoutTests` | `test_timeout_no_confirma_pago` | PASA |
| `MercadoPagoCheckoutTests` | `test_respuesta_sin_url_no_confirma_pago` | PASA |
| `MercadoPagoCheckoutTests` | `test_url_de_salida_no_puede_apuntar_a_un_sitio_ajeno` | FALLA |
| `MercadoPagoCheckoutTests` | `test_url_de_salida_no_admite_http` | FALLA |
| `MercadoPagoCheckoutTests` | `test_respuesta_nula_del_sdk_muestra_error_controlado` | PASA |
| `MercadoPagoCheckoutTests` | `test_reenvio_del_mismo_formulario_no_crea_dos_checkouts` | FALLA |
| `MercadoPagoCheckoutTests` | `test_urls_de_retorno_y_webhook_son_https_canonicas` | PASA |
| `MercadoPagoCheckoutTests` | `test_sin_token_no_inicia_checkout` | FALLA |
| `MercadoPagoCheckoutTests` | `test_checkout_fallido_no_se_confunde_con_pago_pendiente` | FALLA |
| `MercadoPagoCheckoutTests` | `test_sin_secreto_de_confirmacion_no_se_inicia_checkout` | FALLA |
| `MercadoPagoCheckoutTests` | `test_sdk_tiene_timeout_acotado_y_reintentos_controlados` | FALLA |

Huella SHA-256 del archivo de vistas auditado: `67494f2db682e26745b02b711df216702f7baab4bd2250694b96d6118d6e79f3`.
