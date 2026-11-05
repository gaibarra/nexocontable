# Comparación internacional aplicada — 05/11/2026

La sección 03 deja de ser una identificación bibliográfica seguida de una frase.
Se compone en el servidor con alcance, contraste con NIF mexicanas, decisiones,
ejemplo propio, evidencia, fuentes educativas y enlaces oficiales. El desarrollo
se guarda en el contenido y su paquete versionado en la instantánea; editar la
guía no modifica retrospectivamente los documentos ya guardados.

`comparacion-internacional-2026-11-05-v1` cubre los 23 perfiles del estándar. Las
cuentas sin equivalente exclusivo explican por qué y qué hechos deben analizarse,
sin asignar una NIC/NIIF por fuerza. Las referencias internacionales complementan
la revisión; no acreditan adopción de NIIF ni convergencia literal con NIF.

Para Caja/Bancos se distingue NIC 7 (flujos) de C-1 (efectivo) y B-2 (estado de
flujos mexicano); se desarrollan composición, operación/inversión/financiamiento,
métodos directo e indirecto, transferencias propias, partidas no monetarias,
conciliación y revelaciones. El caso propio de Caja concilia 4,000 + 11,600 − 2,400
− 6,000 = 7,200, sin duplicar transferencias internas ni depreciación. Los importes
son ilustrativos, no datos reales. La referencia a la transición de NIIF 18 precisa
vigencia desde periodos anuales iniciados el 01/01/2027 y adopción anticipada,
verificada en la ficha oficial; no declara obligatorio ese cambio para 2026.

Fuentes: comparaciones propias apoyadas en capítulos identificados de
Arnold/Kyle/Lyryx, Intermediate Financial Accounting 2021-A, CC BY 4.0. Para flujos,
volumen 2, secciones 20.1–20.5, páginas impresas 314–343. Se preservan atribución,
licencia y límites; no se reproduce texto IFRS ni citas de terceros. Las fichas
oficiales identifican normas y alcance y no se incorporan como texto completo a
los prompts. No se usan opciones ASPE ni el apéndice 6.6 del volumen 1.

La carga `cargar_comparaciones_internacionales` crea 184 criterios contables
educativos adicionales (23 perfiles × ocho regímenes), sin sobrescribir los 184
criterios del desarrollo mexicano. Selección por perfil, régimen, fecha, permisos,
publicación y retiro. Una comparación solo se incorpora cuando su criterio está
publicado y autorizado; retirarla no modifica instantáneas históricas. Sus fuentes
quedan registradas como usadas aunque la IA no las repita. El formato JSON, el
presupuesto y los intentos de generación no cambian; la sección la compone el
servidor y no depende de una expansión adicional de salida del modelo.

Se identificó un único borrador no aprobado con la referencia NIC 7 indicada por
el usuario: manual 84, Caja 101. Se amplió LOCALMENTE solo su sección 03 y su
trazabilidad. Conserva contenido restante, título, autoría y estado no aprobado;
la versión anterior íntegra queda archivada mediante reformulación. No se enviaron
datos del cliente a IA. El resto de 18 documentos conservó huellas y aprobaciones.

Validación: 296 pruebas de catálogo/cuentas/donativos aprobadas, incluidas cinco
pruebas nuevas sobre desarrollo, publicación idempotente, trazabilidad, retiro,
instantáneas y Word. Se verificaron 13 fichas oficiales con respuesta 200. No se
pretende que esas pruebas certifiquen cumplimiento normativo.

Manual 84: sección internacional de 583 palabras; pantalla a 390/1440 px sin
desbordamiento; PDF navegador de 11 páginas y previsualización de Word con
LibreOffice de 9 páginas, ambos sin texto fuera de página y con enlaces. No se
sustituye revisión en Microsoft Word nativo. Evidencias privadas en
`output/biblioteca/internacional_2026_11_05/`.

Despliegue sin nueva migración ni cambio de assets: cargar comparaciones y
reiniciar ambos Gunicorn; verificar biblioteca activa y acceso autenticado. Las
referencias no comprobadas conservan la revisión profesional requerida. La
reversión retira los nuevos criterios y conserva historial y contenido archivado.
