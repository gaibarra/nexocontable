"""Controles de regresión acotados; no sustituyen una auditoría fiscal o normativa."""
import re
import unicodedata
from bs4 import BeautifulSoup


def texto_normalizado(value):
    text = BeautifulSoup(value or '', 'html.parser').get_text(' ')
    text = ''.join(c for c in unicodedata.normalize('NFKD', text).lower() if not unicodedata.combining(c))
    return re.sub(r'[*_`]', '', text)


def revisar_contenido(contenido, regimen=''):
    hallazgos = []
    def agregar(codigo, mensaje):
        if not any(item['codigo'] == codigo for item in hallazgos):
            hallazgos.append({'codigo': codigo, 'mensaje': mensaje, 'nivel': 'error'})
    for parrafo in re.split(r'\n\s*\n|\n(?=\s*[-*]\s)', contenido or ''):
        texto = texto_normalizado(parrafo)
        vincula_cero = re.search(r'(?:0\s*%|tasa cero).{0,50}(?:en|por).{0,25}fronter|fronter.{0,65}(?:aplica|tasa de|al|es).{0,20}0\s*%', texto)
        niega_cero = re.search(r'no.{0,35}(?:determina|implica|equivale|corresponde)|distint[oa]s?|no confundir', texto)
        if vincula_cero and not niega_cero:
            agregar('iva_fronterizo', 'La ubicación fronteriza no implica IVA a tasa cero; verificar el estímulo de 8% y sus requisitos.')
        niega_atribucion = re.search(r'no.{0,80}(?:atrib|invoc|fundament)|no\s+(?:es|son)\s+(?:la|el)\s+fundamento', texto)
        if re.search(r'(?:art(?:iculo)?\.?\s*)?27\b.{0,35}\bxi(?:i)?\b', texto) and re.search(r'metodo|valuacion|peps|promedio', texto) and not niega_atribucion:
            agregar('lisr_metodos', 'Revisar los métodos fiscales de valuación en LISR artículo 41; no atribuirlos al artículo 27 XI/XII.')
        if re.search(r'(?:art(?:iculo)?\.?\s*)?28\b.{0,35}xiii\b', texto) and re.search(r'merma|destruc|deterior', texto) and not niega_atribucion:
            agregar('lisr_mermas', 'El artículo 28 XIII no fundamenta mermas o destrucción de inventarios; revisar LISR 27 XX y requisitos aplicables.')
        if re.search(r'27\b.{0,25}\bxx\b.{0,75}(?:regula|deduccion|perdida).{0,40}creditos? incobrables?', texto):
            agregar('lisr_27_xx', 'LISR 27 XX corresponde a pérdida de valor de mercancías; los créditos incobrables se analizan en 27 XV.')
        if re.search(r'27\b.{0,25}\bxx\b.{0,170}(?:obligacion de conservar|obligacion.{0,25}documentacion comprobatoria)', texto):
            agregar('lisr_27_xx_documentos', 'LISR 27 XX no es una regla general de conservación de documentación; revisar el fundamento pertinente.')
        if re.search(r'(?:articulo|art\.)\s*41.{0,160}costeo directo', texto) and not re.search(r'no.{0,30}costeo directo|costeo directo.{0,12}no\b', texto):
            agregar('lisr_41_directo', 'El costeo directo no figura entre las opciones del artículo 41: PEPS, costo identificado, costo promedio y detallista.')
        if re.search(r'(?:niif|ifrs)\s*13', texto) and re.search(r'neto realizable|neto de realizacion|valor de realizacion neto', texto) and not re.search(r'distint[oa]|diferente|no\s+(?:es|equivale|se utiliza|debe|usar)|no.{0,45}(?:base|fundament|sustitu)', texto):
            agregar('vnr_valor_razonable', 'Distinguir el valor neto realizable de NIC 2 del valor razonable; NIIF 13 no fundamenta el VNR ordinario.')
        if regimen == 'pf_resico':
            afirma_deduccion = re.search(r'costos? deducibles?|deduccion(?:es)? por deterioro|no es deducible hasta|efecto fiscal se difiere|deducir.{0,25}(?:costo|deterioro)', texto)
            separa_isr = re.search(r'(?:sin aplicar|no (?:se aplican|proceden|se deducen|son deducibles|disminuye)).{0,50}deduc|no.{0,70}(?:isr|base resico)', texto)
            if afirma_deduccion and not separa_isr:
                agregar('resico_deducciones', 'En RESICO persona física, separar el gasto contable del ISR sobre ingresos cobrados sin deducciones y del análisis independiente del IVA.')
    return hallazgos
