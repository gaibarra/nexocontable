# Informe Inicial de Revisión de Producto y Arquitectura
## Manual Contable AI

**Dirigido a:** Director de Desarrollo de Productos de Proyecto G40  
**C.P. Gonzalo Arturo Ibarra Mendoza**  
**Fecha:** 10 de junio de 2026

---

## 1. Propósito del documento

El presente documento plasma el resultado de una revisión funcional y técnica profunda de la aplicación Manual Contable AI, como preparación para una siguiente etapa de optimización orientada a incrementar su utilidad práctica para despachos contables en México.

El análisis se enfocó en dos dimensiones complementarias:

1. Utilidad contable real para despachos y organizaciones mexicanas.
2. Solidez de arquitectura de software para soportar crecimiento, control y operación.

El objetivo no es únicamente evaluar si la aplicación funciona, sino determinar si puede evolucionar de un MVP funcional a una plataforma de trabajo útil, defendible y escalable para la operación documental-contable de un despacho.

---

## 2. Resumen ejecutivo

Manual Contable AI cuenta hoy con una base funcional sólida de tipo SaaS multi-tenant orientada a contadores en México. La aplicación ya resuelve un flujo valioso:

1. Registro de usuario profesional.
2. Alta de organización o cliente.
3. Carga de catálogo de cuentas.
4. Validación contra Código Agrupador SAT.
5. Generación de manuales contables con IA.
6. Edición, aprobación y consulta de manuales.
7. Gestión básica de equipo.
8. Recepción de donativos por Mercado Pago.

Desde la perspectiva de negocio, la solución ya tiene una propuesta útil: **ahorrar tiempo en la elaboración de manuales contables y criterios documentales por cliente**.

Sin embargo, desde la perspectiva de utilidad práctica para un despacho contable, el producto todavía está más cerca de un **generador documental asistido** que de una **plataforma integral de control técnico-contable**.

El principal hallazgo es que la aplicación tiene un núcleo correcto y con potencial, pero para convertirse en una herramienta de alto valor para despachos en México necesita fortalecerse en cinco frentes:

1. Gobierno de permisos y segregación de funciones.
2. Trazabilidad documental y versionado.
3. Operación práctica del expediente contable-fiscal.
4. Automatización robusta del catálogo SAT y onboarding.
5. Escalabilidad técnica para procesos de IA.

---

## 3. Diagnóstico general del producto

### 3.1 Qué resuelve bien hoy

La plataforma ya resuelve varias necesidades reales de un contador o despacho:

- Administración de múltiples organizaciones o clientes desde una sola cuenta.
- Carga masiva de catálogos por CSV o Excel.
- Relación de cuentas con Código Agrupador SAT.
- Generación contextual de manuales contables por giro y régimen fiscal.
- Edición y aprobación de manuales.
- Incorporación de colegas al tenant mediante invitación segura.
- Base técnica razonable para una plataforma SaaS pequeña o mediana.

### 3.2 Qué limita hoy su valor para un despacho

Aunque el flujo es funcional, todavía faltan elementos críticos para operación profesional:

- No existe control documental fino por versiones.
- No existe bitácora de quién aprobó, editó o cambió un manual.
- No hay un expediente estructurado de evidencia por cuenta.
- No hay flujo formal de revisión por niveles del despacho.
- No hay diferenciación efectiva entre lectura, captura, revisión y aprobación.
- La generación con IA todavía corre de manera síncrona en la solicitud web.
- La carga inicial del catálogo SAT no está automatizada dentro del proyecto.

---

## 4. Hallazgos principales

### 4.1 Hallazgo 1: La promesa de roles existe, pero el control efectivo todavía no

#### Lectura contable

En un despacho contable, la segregación de funciones es importante. No es lo mismo:

- quien captura
- quien revisa
- quien aprueba
- quien solo consulta

Hoy el sistema ya define roles como:

- Propietario
- Contador
- Auxiliar
- Solo lectura

Eso es correcto como diseño funcional inicial. Sin embargo, en la práctica, varias operaciones críticas todavía dependen básicamente de estar autenticado y tener tenant activo.

#### Lectura de arquitectura

Esto significa que la capa de autorización aún no está centralizada ni aplicada de forma consistente. El sistema ya conoce el rol del usuario, pero no lo usa todavía como política transversal de acceso.

#### Implicación

Para un despacho, esto representa riesgo operativo, porque podría haber acciones de modificación o aprobación realizadas por perfiles que en términos de control interno no deberían ejecutarlas.

#### Valor de corregirlo

Resolver esto elevaría de inmediato la credibilidad del producto frente a despachos que necesitan:

- orden operativo
- control de cambios
- trazabilidad de responsabilidad
- separación entre elaboración y aprobación

### 4.2 Hallazgo 2: El manual generado todavía es un documento, no un expediente técnico-contable

#### Lectura contable

Un despacho rara vez necesita únicamente texto redactado. Lo que realmente necesita es un entregable defendible y reutilizable que incluya:

- política contable
- criterio fiscal
- evidencia requerida
- responsable
- vigencia
- aprobación
- soporte documental asociado

Hoy la aplicación genera un contenido útil y bien orientado, especialmente por su énfasis en materialidad y razón de negocios. Eso tiene valor. Pero todavía falta que ese contenido se convierta en un **expediente operativo**.

#### Lectura de arquitectura

El modelo actual de manual es todavía simple. No conserva formalmente:

- versión
- estatus detallado
- observaciones
- aprobador
- fecha de aprobación
- ejercicio fiscal
- vigencia
- historial de cambios
- fundamento normativo congelado por versión

#### Implicación

Eso limita el uso del sistema en escenarios donde el despacho necesita demostrar qué criterio aplicó, cuándo lo emitió y bajo qué versión quedó aprobado.

#### Valor de corregirlo

Convertir el manual en expediente haría que la plataforma no solo ayude a redactar, sino a **gobernar criterio contable y fiscal**.

### 4.3 Hallazgo 3: Falta aterrizar la utilidad práctica para auxiliares y revisores

#### Lectura contable

La gran oportunidad del producto no está únicamente en escribir manuales, sino en volver operable el cumplimiento documental del cliente. En México, una parte importante del trabajo del despacho consiste en pedir, validar y resguardar evidencia para soportar operaciones.

El sistema ya apunta correctamente hacia:

- materialidad
- razón de negocios
- entregables documentales
- riesgos fiscales

Sin embargo, el resultado aún se concentra en contenido narrativo.

#### Lo que falta para el despacho

El producto ganaría mucho valor si además generara:

- checklists por cuenta
- listas de soporte por operación
- requerimientos para cliente
- validaciones documentales por rubro
- seguimiento de faltantes
- evidencia por periodo

#### Lectura de arquitectura

Esto implica pasar de un modelo centrado en documentos a un modelo mixto de:

- documentos generados
- tareas operativas
- controles documentales
- estados de cumplimiento

### 4.4 Hallazgo 4: La carga del catálogo SAT es un cuello de botella de puesta en marcha

#### Lectura contable

Si el sistema valida cuentas contra el Código Agrupador SAT, entonces ese catálogo base debe existir desde el día uno. De otro modo, el usuario llega a la plataforma y no puede aprovechar el flujo completo sin intervención manual.

#### Lectura de arquitectura

Actualmente no se identificó un mecanismo integrado de carga inicial mediante:

- fixture
- comando de management
- archivo base oficial incluido
- proceso de seed documentado y repetible

#### Implicación

Esto debilita:

- onboarding
- despliegue
- repetibilidad
- soporte
- confiabilidad del entorno

#### Valor de corregirlo

Automatizar la carga del catálogo SAT resolvería un problema pequeño técnicamente, pero muy importante desde producto y operación.

### 4.5 Hallazgo 5: La IA está bien orientada, pero la arquitectura de ejecución aún es de MVP

#### Lectura contable

Para el usuario final, que un manual tarde demasiado o falle en momentos de carga afecta la percepción de confiabilidad. En un despacho, la herramienta debe sentirse estable, no experimental.

#### Lectura de arquitectura

La generación de manuales aún corre de manera síncrona dentro del request web. Eso significa que el usuario queda amarrado al tiempo de respuesta de la IA.

#### Riesgos

- espera prolongada
- timeouts
- saturación de workers
- mala experiencia si varios usuarios generan documentos a la vez

#### Valor de corregirlo

Mover la generación a tareas asíncronas permitiría:

- mayor estabilidad
- mejor experiencia de usuario
- reintentos controlados
- trazabilidad del proceso
- mejor escalabilidad operativa

---

## 5. Valor actual para despachos contables en México

A pesar de las brechas, la aplicación sí tiene una base con valor real para despachos, especialmente en estos escenarios:

### 5.1 Estandarización documental por cliente

Un despacho que atiende múltiples organizaciones necesita criterios homogéneos. La estructura multi-tenant ayuda a separar clientes y mantener su información independiente.

### 5.2 Ahorro de tiempo en elaboración de manuales

El uso de IA contextualizada por giro y régimen puede reducir tiempo en documentación inicial y actualización de manuales internos.

### 5.3 Enfoque correcto hacia materialidad y sustancia económica

Ese ángulo es especialmente relevante para México. Pocas herramientas atacan de frente la utilidad documental con lenguaje cercano a riesgos fiscales reales.

### 5.4 Coordinación básica de equipo

El módulo de invitaciones y membresías ya abre la puerta a trabajar por despacho y no solo por usuario individual.

---

## 6. Oportunidades de producto de alto valor para Proyecto G40

A continuación se listan las oportunidades más valiosas, pensando en despachos contables mexicanos y en la evolución del producto hacia una plataforma profesional.

### 6.1 Convertir manuales en expedientes contables y fiscales

En lugar de quedarse en un texto, cada manual debe evolucionar hacia un expediente con:

- datos del cliente
- ejercicio fiscal
- versión
- estatus
- revisor
- aprobador
- vigencia
- evidencia asociada
- observaciones

### 6.2 Generar checklists de evidencia por cuenta o rubro

Ejemplos:

- Bancos
- Clientes
- Anticipos
- Proveedores
- Gastos de viaje
- Servicios especializados
- Partes relacionadas
- Ingresos
- Nómina

Esto es más útil para un despacho que un texto largo, porque aterriza la ejecución del trabajo diario.

### 6.3 Formalizar flujo de revisión interna

Modelo sugerido:

- Borrador
- En revisión
- Observado
- Corregido
- Aprobado
- Vencido

Esto refleja mejor la práctica de un despacho que el esquema actual de aprobado/no aprobado.

### 6.4 Versionado por ejercicio fiscal y por cambio normativo

Un cliente puede requerir una versión 2025, otra 2026 o una actualización por cambio de criterio, régimen o giro. El despacho necesita comparar, rastrear y conservar versiones.

### 6.5 Solicitudes de soporte al cliente

La plataforma podría emitir listas de documentación faltante:

- contrato
- CFDI
- XML
- entregable
- evidencia de prestación
- estado de cuenta
- autorización interna
- papel de trabajo

Esto la convertiría en una herramienta de coordinación despacho-cliente.

### 6.6 Plantillas base por giro y régimen

Ejemplos de alto valor:

- comercializadora
- servicios profesionales
- construcción
- restaurante
- asociación civil
- RESICO
- arrendamiento
- salud
- educativo

Esto reduce trabajo repetitivo y mejora el arranque por cliente.

### 6.7 Semáforos de riesgo fiscal-documental

Si la plataforma ya conoce el catálogo, puede señalar cuentas más sensibles por evidencia y materialidad.

Ejemplos:

- honorarios
- viáticos
- efectivo
- anticipos
- servicios especializados
- operaciones con partes relacionadas
- ingresos atípicos

### 6.8 Exportables profesionales

Más allá de imprimir en PDF, conviene entregar:

- PDF con control documental
- índice
- firma o revisión
- anexos
- versión Word para trabajo interno
- portada institucional del despacho

---

## 7. Siguientes pasos naturales
## Explicados en términos contables y de arquitectura de software

### Paso 1. Cerrar control de permisos y segregación de funciones

#### En términos contables

Este paso equivale a formalizar quién puede:

- capturar
- editar
- revisar
- aprobar
- solo consultar

Es un equivalente digital de fortalecer control interno y evitar que una misma persona haga todas las funciones críticas sin supervisión.

#### En términos de arquitectura de software

Se requiere implementar una capa de autorización consistente basada en rol y tipo de acción. No basta con que el sistema sepa el rol; debe usarlo para decidir acceso en todas las operaciones sensibles.

#### Resultado esperado

- Menor riesgo operativo
- Coherencia entre roles prometidos y reales
- Base sólida para flujos de revisión posteriores

#### Prioridad

**Crítica**

### Paso 2. Convertir el manual en expediente versionado

#### En términos contables

Un criterio contable o fiscal útil no debe existir como texto suelto, sino como documento controlado, con responsable, vigencia y evidencia de aprobación.

Este paso equivale a pasar de una minuta técnica a un documento institucional del despacho.

#### En términos de arquitectura de software

Se requiere ampliar el modelo de datos para incluir:

- versión
- estatus
- ejercicio fiscal
- vigencia
- aprobador
- fecha de aprobación
- historial de cambios
- observaciones

#### Resultado esperado

- Trazabilidad
- Reutilización
- Auditoría interna
- Mayor confianza del despacho

#### Prioridad

**Crítica**

### Paso 3. Transformar la salida de IA en herramienta operativa

#### En términos contables

El despacho necesita ejecutar trabajo, no solo leer recomendaciones. Por eso conviene que la IA genere también:

- checklists
- solicitudes de soporte
- evidencia requerida
- controles por cuenta
- tareas pendientes

#### En términos de arquitectura de software

Esto implica separar dos tipos de salida:

1. Contenido narrativo.
2. Estructuras operativas reutilizables.

La aplicación debería almacenar no solo texto, sino también listas, campos y estados de cumplimiento.

#### Resultado esperado

- Más utilidad diaria para auxiliares y contadores
- Menor dependencia de interpretación manual
- Mejor seguimiento de documentación faltante

#### Prioridad

**Alta**

### Paso 4. Automatizar la carga del catálogo SAT y el onboarding técnico

#### En términos contables

El usuario debe poder empezar a trabajar sin depender de cargas manuales del catálogo base. Si el catálogo SAT es requisito del flujo, debe estar listo desde el arranque.

#### En términos de arquitectura de software

Se requiere definir un mecanismo repetible de seed inicial mediante:

- fixture
- comando de management
- archivo fuente controlado
- documentación de inicialización

#### Resultado esperado

- Onboarding confiable
- Instalaciones repetibles
- Menor fricción de soporte
- Menor dependencia operativa del equipo técnico

#### Prioridad

**Alta**

### Paso 5. Formalizar workflow de revisión del despacho

#### En términos contables

La mayoría de los despachos operan por niveles: auxiliar, contador, supervisor, socio. El sistema debe reflejar esa realidad con estados y responsables.

#### En términos de arquitectura de software

Se requiere modelar un workflow explícito con transiciones válidas de estado y reglas por rol.

Ejemplo:

- auxiliar redacta
- contador revisa
- socio aprueba
- sistema registra bitácora

#### Resultado esperado

- Mejor control interno
- Evidencia de revisión
- Producto más alineado a práctica real de despacho

#### Prioridad

**Alta**

### Paso 6. Mover la generación con IA a procesamiento asíncrono

#### En términos contables

El usuario necesita continuidad operativa. No conviene que la herramienta se quede pensando durante demasiado tiempo o falle si el documento es grande.

#### En términos de arquitectura de software

Se requiere desacoplar la generación del request web y pasarla a un esquema de tareas en segundo plano con:

- cola
- reintentos
- registro de estatus
- notificación de resultado

#### Resultado esperado

- Mejor experiencia de usuario
- Mayor estabilidad
- Base para escalar volumen

#### Prioridad

**Alta**

### Paso 7. Incorporar bitácora y trazabilidad completa

#### En términos contables

Toda modificación relevante debe dejar huella:

- quién cambió
- qué cambió
- cuándo cambió
- por qué cambió

Eso fortalece control interno, revisión y defensa documental.

#### En términos de arquitectura de software

Conviene introducir eventos o tablas de auditoría para acciones críticas:

- alta de cuenta
- modificación de cuenta
- eliminación de cuenta
- generación de manual
- edición de manual
- aprobación
- eliminación
- invitaciones y cambios de membresía

#### Resultado esperado

- Mayor gobernanza
- Soporte a cumplimiento
- Mejor capacidad de revisión posterior

#### Prioridad

**Alta**

### Paso 8. Construir una biblioteca de plantillas por industria y régimen

#### En términos contables

Muchos clientes comparten patrones. Un despacho gana productividad cuando parte de plantillas razonables por tipo de negocio y no desde cero en cada caso.

#### En términos de arquitectura de software

Esto sugiere una capa de plantillas maestras desacoplada del tenant, reutilizable y parametrizable por:

- giro
- régimen
- tamaño de empresa
- tipo de operación

#### Resultado esperado

- Menor tiempo de arranque por cliente
- Mayor consistencia técnica
- Escalabilidad comercial del producto

#### Prioridad

**Media-Alta**

---

## 8. Recomendación de priorización

### Fase 1. Fortalecimiento estructural

Objetivo: asegurar control y confiabilidad.

- permisos por rol
- carga automática del catálogo SAT
- bitácora mínima
- workflow básico de revisión
- versionado inicial de manuales

### Fase 2. Utilidad operativa para el despacho

Objetivo: convertir texto en herramienta de trabajo.

- checklists de evidencia
- solicitudes de soporte al cliente
- estados de cumplimiento documental
- plantillas por rubro crítico

### Fase 3. Escalabilidad y diferenciación

Objetivo: preparar crecimiento y valor competitivo.

- colas asíncronas para IA
- comparativo entre versiones
- semáforos de riesgo
- exportables profesionales
- biblioteca sectorial avanzada

---

## 9. Evaluación final

Manual Contable AI no es una maqueta. Ya existe una base real, funcional y bien encaminada, con una arquitectura de monolito Django modular suficiente para una primera etapa de crecimiento.

La principal conclusión del análisis es la siguiente:

> El producto ya tiene un núcleo valioso para despachos contables en México, pero su siguiente evolución natural no debe centrarse solo en generar mejores textos, sino en convertirse en una plataforma de control técnico, documental y operativo.

En otras palabras:

- hoy genera manuales
- mañana debe ayudar a gobernarlos
- después debe ayudar a ejecutarlos
- finalmente debe ayudar a defenderlos

Ahí es donde existe mayor valor para Proyecto G40.

---

## 10. Recomendación ejecutiva para revisión inicial

Se recomienda que la siguiente conversación de producto con Dirección se estructure alrededor de esta pregunta:

**¿Queremos que Manual Contable AI sea principalmente un generador de contenido técnico, o queremos que evolucione hacia un sistema de gestión documental-contable para despachos?**

La respuesta a esa pregunta cambia la priorización de arquitectura, modelo de datos, UX, trazabilidad y roadmap comercial.

La evidencia del análisis sugiere que el mayor valor está en la segunda opción.

---

## 11. Propuesta de siguiente discusión directiva

Para la revisión inicial por parte de Dirección de Desarrollo de Productos, conviene validar estas decisiones:

1. Si el producto se posicionará como herramienta para despacho o como herramienta individual para contador.
2. Si la prioridad inmediata será control interno y trazabilidad.
3. Si el siguiente entregable debe ser un expediente versionado en lugar de un manual simple.
4. Si el flujo de trabajo del despacho será modelado formalmente en el sistema.
5. Si la capa de IA será evolucionada hacia checklists y evidencia operativa.
6. Si se iniciará una biblioteca de plantillas sectoriales como línea de diferenciación comercial.

---

**Documento preparado para revisión inicial de producto y arquitectura.**