"""Presentación editorial derivada: conserva el texto financiero y sus importes."""
import re
from bs4 import NavigableString, Tag

LEYES = [
    ('LISR', 'Ley del Impuesto sobre la Renta', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf', r'Ley\s+del\s+Impuesto\s+sobre\s+la\s+Renta|\bLISR\b'),
    ('LIVA', 'Ley del Impuesto al Valor Agregado', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf', r'Ley\s+del\s+Impuesto\s+al\s+Valor\s+Agregado|\bLIVA\b'),
    ('CFF', 'Código Fiscal de la Federación', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf', r'C[oó]digo\s+Fiscal\s+de\s+la\s+Federaci[oó]n|\bCFF\b'),
]
IMPORTANTES = re.compile(r'\b(?:no\s+(?:causa|genera)\s+IVA|no\s+representa\s+ISR\s+causado|sin\s+deducci[oó]n\s+alguna|activo\s+por\s+impuesto\s+diferido|pasivo\s+por\s+impuesto\s+diferido|diferencias?\s+temporales?|diferencias?\s+permanentes?|bases?\s+fiscales?|valores?\s+contables?|valor\s+contable|tasa\s+hipot[eé]tica|tasa\s+ilustrativa|recuperabilidad|valor\s+neto\s+realizable|supuestos?\s+ilustrativos?|hechos\s+por\s+validar|revisi[oó]n\s+profesional)\b', re.I)


def _enlace(soup, texto, ley):
    a=soup.new_tag('a',href=ley[2],title=ley[1]+' — texto oficial en Cámara de Diputados',target='_blank',rel='noopener noreferrer')
    a['class']=['document-law-link'];a.string=texto
    return a


def _leyes(soup):
    usadas=[]
    for ley in LEYES:
        patron=re.compile(re.escape(ley[2])+'|'+ley[3],re.I)
        if not patron.search(soup.get_text(' ')):continue
        usadas.append(ley)
        for node in list(soup.find_all(string=patron)):
            if node.find_parent(['a','pre','code','h1','h2','h3','h4']):continue
            partes=[];inicio=0
            for match in patron.finditer(str(node)):
                if match.start()>inicio:partes.append(NavigableString(str(node)[inicio:match.start()]))
                partes.append(_enlace(soup,match.group(0),ley));inicio=match.end()
            if inicio<len(node):partes.append(NavigableString(str(node)[inicio:]))
            for parte in partes:node.insert_before(parte)
            node.extract()
    # El texto original de una URL oficial se conserva, pero ahora es pulsable.
    for ley in usadas:
        patron=re.compile(re.escape(ley[2]))
        for node in list(soup.find_all(string=patron)):
            if node.find_parent(['a','pre','code']):continue
            partes=patron.split(str(node))
            for i,parte in enumerate(partes):
                if i:node.insert_before(_enlace(soup,ley[2],ley))
                if parte:node.insert_before(NavigableString(parte))
            node.extract()
    return usadas


def _listas(soup):
    for p in list(soup.find_all('p')):
        if p.find_parent(class_='document-fundamentos') or p.find(True):continue
        t=p.get_text()
        marcas=list(re.finditer(r'(?<!\w)(\d{1,2})[.)]\s+',t))
        if len(marcas)<3 or [int(m[1]) for m in marcas]!=list(range(1,len(marcas)+1)):continue
        # No interpreta como lista las cifras de decimales ni localizaciones normativas.
        if any(m.start()>0 and t[m.start()-1] not in ':; \n' for m in marcas):continue
        prefix=t[:marcas[0].start()].strip()
        if len(prefix)>100:continue
        lista=soup.new_tag('ol');lista['class']=['document-policy-list']
        for i,m in enumerate(marcas):
            fin=marcas[i+1].start() if i+1<len(marcas) else len(t)
            item=soup.new_tag('li');item.string=t[m.end():fin].strip();lista.append(item)
        if prefix:
            etiqueta=soup.new_tag('p');etiqueta.string=prefix;p.insert_before(etiqueta)
        p.replace_with(lista)


def _negritas(soup):
    for bloque in soup.find_all(['p','li']):
        if bloque.find_parent(class_='document-fundamentos') or bloque.find_parent(class_='document-laws'):continue
        disponibles=3
        for node in list(bloque.find_all(string=True)):
            if disponibles<=0:break
            if node.find_parent(['strong','b','a','pre','code','table']):continue
            t=str(node);matches=list(IMPORTANTES.finditer(t))[:disponibles]
            if not matches:continue
            inicio=0
            for m in matches:
                if m.start()>inicio:node.insert_before(NavigableString(t[inicio:m.start()]))
                strong=soup.new_tag('strong');strong.string=m.group(0);node.insert_before(strong);inicio=m.end();disponibles-=1
            if inicio<len(t):node.insert_before(NavigableString(t[inicio:]))
            node.extract()


def estilizar(soup):
    _listas(soup)
    usadas=_leyes(soup)
    _negritas(soup)
    for n,h in enumerate(soup.find_all('h2'),1):
        # La numeración es visual y compartida con la exportación; el contenido guardado no cambia.
        primero=h.find(string=True)
        if primero is not None:
            primero.replace_with(NavigableString(re.sub(r'^\d+[.)](?:\s+|$)','',str(primero))))
        h.insert(0,NavigableString(f'{n:02d}  '))
        h['class']=['document-section-heading'];h['id']=f'document-section-{n}'
    for p in soup.find_all('p'):
        if p.get_text(strip=True).startswith('Fundamentos:'):p['class']=['document-citation']
    for tabla in soup.find_all('table'):
        cabeceras=[c.get_text(' ',strip=True).lower() for c in tabla.select('thead th')]
        if cabeceras==['cuenta','debe','haber']:
            tabla['class']=list(tabla.get('class',[]))+['document-entry-table']
        for fila in tabla.find_all('tr'):
            celdas=fila.find_all(['td','th'],recursive=False)
            if celdas and re.fullmatch(r'total(?:es)?',celdas[0].get_text(strip=True),re.I):
                fila['class']=['document-total-row']
                for c in celdas:
                    if not c.find('strong'):
                        strong=soup.new_tag('strong')
                        for child in list(c.contents):strong.append(child.extract())
                        c.append(strong)
    if usadas:
        panel=soup.new_tag('section',attrs={'class':'document-laws','aria-label':'Acceso a las leyes citadas'})
        h=soup.new_tag('h3');h.string='Legislación citada · Acceso oficial';panel.append(h)
        ul=soup.new_tag('ul')
        for ley in usadas:
            li=soup.new_tag('li');a=_enlace(soup,ley[0]+' — '+ley[1],ley);li.append(a);ul.append(li)
        panel.append(ul)
        nota=soup.new_tag('p');nota.string='Textos oficiales publicados por la Cámara de Diputados. Contrasta la versión consultada y el periodo aplicable.';panel.append(nota)
        fuentes=soup.find('section',class_='document-fundamentos')
        if fuentes:
            cabecera=fuentes.find('h2');cabecera.insert_after(panel) if cabecera else fuentes.insert(0,panel)
        else:soup.append(panel)
    return soup
