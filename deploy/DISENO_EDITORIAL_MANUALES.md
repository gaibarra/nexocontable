# Diseño editorial de manuales — 29/10/2026

Se aplica una composición profesional común a pantalla y exportación: paleta
azul marino/verde petróleo, título descriptivo, secciones numeradas, tipografía
más legible, separación de referencias y tablas con encabezados, totales y
alineación numérica. La impresión usa encabezados de tabla claros con texto oscuro
para conservar legibilidad incluso sin gráficos de fondo.

El compositor destaca hasta tres coincidencias por bloque de conceptos relevantes,
conservando las negaciones, cifras y negritas existentes. Convierte enumeraciones
simples consecutivas en listas reales sin interpretar decimales o citas como listas.
El contenido almacenado, sus fuentes, autoría y aprobación permanecen intactos.

Las menciones de LISR, LIVA y CFF y sus nombres completos enlazan a los PDF oficiales
de Cámara de Diputados. Un bloque de Legislación citada reúne únicamente las leyes
aludidas. Las URL oficiales existentes pasan a ser enlaces completos. No se anidan
hipervínculos ni se cargan recursos externos para verificar/exportar documentos.

Word incorpora hipervínculos reales, subrayado y color de enlace, énfasis en negrita,
encabezados y sombreado de tablas; la columna de cuenta dispone de 60% del ancho
en asientos simples y las cifras se alinean a la derecha.

Validación: 277 pruebas de cuentas/catálogo/donativos en PostgreSQL aislado; 22
pruebas dirigidas de presentación/exportación y 5 de enlaces/estilo aprobadas
sin contarlas doble. Revisión local a 390 y 1440 píxeles sin desbordamiento.
PDF de navegador con anotaciones URI a las tres leyes oficiales; DOCX con
relaciones Hyperlink verificadas. Revisión de previsualización Word mediante
LibreOffice, sin afirmar validación en Microsoft Word nativo.

En el manual 79: PDF de navegador de 7 páginas y previsualización Word de 6 páginas,
sin texto fuera de página, con negritas, listas y enlaces. Evidencias privadas en
output/biblioteca/desarrollo_completo/. También se comprobó una salida PDF sin
fondos. El diseño es una transformación de salida, no una nueva generación IA.

Despliegue: collectstatic y reinicio de ambos servicios; CSS versionado editorial-1.
