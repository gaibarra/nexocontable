from pathlib import Path
from io import BytesIO
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.pdf-libs'))
import cairosvg
import qrcode
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
URL = 'https://manualcontable.online/registro/'
for name, file in [('Lato', 'Lato-Regular.ttf'), ('LatoBold', 'Lato-Bold.ttf'), ('LatoHeavy', 'Lato-Heavy.ttf')]:
    pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/lato/' + file))
navy, blue, green, muted = map(HexColor, ['#15324F', '#2464A0', '#27845B', '#526577'])
c = canvas.Canvas(str(HERE / 'Invitacion_NexoContable_Comunidad_Contable_Mexico.pdf'), pagesize=(612, 792))
c.setTitle('Únete a NexoContable | Comunidad contable de México')
c.setAuthor('NexoContable')
c.setSubject('Invitación a capacitar auxiliares contables y fortalecer la cultura de aplicación de las NIF')

def text(x, y, s, size=11, font='Lato', color=navy):
    c.setFillColor(color); c.setFont(font, size); c.drawString(x, y, s)

def para(x, top, width, s, size=10.5, leading=14, color=muted, bold=False):
    p = Paragraph(s, ParagraphStyle('p', fontName='LatoBold' if bold else 'Lato', fontSize=size, leading=leading, textColor=color))
    _, h = p.wrap(width, 500)
    p.drawOn(c, x, top-h)
    return h

c.setFillColor(white); c.rect(0, 0, 612, 792, fill=1, stroke=0)
c.setFillColor(green); c.rect(0, 786, 612, 6, fill=1, stroke=0)
logo = cairosvg.svg2png(url=str(ROOT/'static/img/nexocontable-logo-horizontal.svg'), output_width=980)
symbol = Image.open(BytesIO(logo)).crop((0, 0, 226, 220))
c.drawImage(ImageReader(symbol), 29, 731, width=47, height=46, mask='auto')
text(80, 750, 'NexoContable', 22, 'LatoBold', navy)
text(81, 736, 'Conocimiento para tu práctica contable', 7.2, 'Lato', muted)
text(397, 749, 'COMUNIDAD CONTABLE', 8.4, 'LatoBold', muted)
text(529, 735, 'MÉXICO', 8.4, 'LatoBold', green)

text(34, 698, 'Compartamos conocimiento.', 27, 'LatoHeavy')
text(34, 666, 'Fortalezcamos nuestra profesión.', 27, 'LatoHeavy')
para(34, 649, 544, 'Invitamos a contadores, despachos, docentes y auxiliares de todo México a unirse a <b>NexoContable</b>: una herramienta para aprender, documentar y aplicar el criterio contable con apoyo de inteligencia artificial.', 11.5, 15.5)

photo = Image.open(HERE/'capacitacion_contable.png')
photo = ImageOps.fit(photo, (1632, 570), centering=(0.5, 0.03))
c.drawImage(ImageReader(photo), 34, 404, width=544, height=190)
c.setFillColor(navy); c.rect(34, 404, 544, 27, fill=1, stroke=0)
text(47, 413, 'La experiencia se comparte. El criterio contable se construye.', 11, 'LatoBold', white)

cards = [
 ('01', 'Capacita a tus auxiliares', 'Usa ejemplos y manuales como apoyo para explicar cuentas, políticas y tratamientos contables.'),
 ('02', 'Lleva las NIF a la práctica', 'Revisa el sustento de cada tratamiento y fortalece el hábito de fundamentar las decisiones.'),
 ('03', 'Documenta con tu equipo', 'Genera manuales por organización y cuenta; revísalos, adáptalos y expórtalos a Word.'),
]
for i, (n, title, desc) in enumerate(cards):
    x = 34 + i*185
    c.setFillColor(HexColor('#F0F5F8')); c.roundRect(x, 262, 174, 126, 9, fill=1, stroke=0)
    c.setFillColor(green); c.circle(x+21, 366, 11, fill=1, stroke=0)
    text(x+14, 362, n, 8.5, 'LatoBold', white)
    para(x+12, 345, 151, title, 11.3, 14, navy, True)
    para(x+12, 307, 150, desc, 10, 13)

text(34, 239, 'Hagamos de las NIF una cultura de trabajo.', 17, 'LatoHeavy', green)
para(34, 227, 544, 'Integremos las <b>Normas de Información Financiera (NIF)</b> a la capacitación diaria: comprender el porqué de cada registro, documentar las políticas y revisar los casos en equipo.', 10.7, 14)

c.setFillColor(navy); c.roundRect(34, 64, 544, 105, 12, fill=1, stroke=0)
text(51, 145, 'Únete hoy a NexoContable', 20, 'LatoHeavy', white)
text(51, 126, 'Crea tu cuenta gratis y comienza a explorar.', 11, 'Lato', white)
c.setFillColor(HexColor('#4CC491')); c.roundRect(51, 85, 334, 27, 6, fill=1, stroke=0)
text(62, 94, 'manualcontable.online/registro/', 13, 'LatoBold', navy)
c.linkURL(URL, (51, 85, 385, 112), relative=0, thickness=0)
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4, box_size=8)
qr.add_data(URL); qr.make(fit=True)
qr_img = qr.make_image(fill_color='#15324F', back_color='white').convert('RGB')
qr_img.save(HERE/'qr_registro.png')
c.drawImage(ImageReader(qr_img), 476, 82, 75, 75)
c.linkURL(URL, (476, 82, 551, 157), relative=0, thickness=0)
text(480, 72, 'Escanea y únete', 8, 'Lato', white)

para(34, 51, 544, 'Los contenidos generados con IA requieren revisión profesional y consulta de las NIF vigentes. La plataforma es gratuita y se sostiene con donativos voluntarios.', 8, 10, muted)
c.showPage(); c.save()
print(HERE/'Invitacion_NexoContable_Comunidad_Contable_Mexico.pdf')
