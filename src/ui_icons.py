"""Original vector icons for common CAD tools; no vendor artwork."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer


def icon_for(label):
    body='<path d="M10 24 32 12 54 24 54 48 32 60 10 48Z" fill="#b8cce2"/><path d="M10 24 32 36 54 24M32 36V60" fill="none"/>'
    if 'Zylinder' in label:body='<path d="M12 18V48C12 62 52 62 52 48V18Z" fill="#b8cce2"/><ellipse cx="32" cy="18" rx="20" ry="10" fill="#e3edf6"/>'
    elif 'Bohr' in label:body+='<ellipse cx="32" cy="24" rx="10" ry="5" fill="white"/><path d="M22 24v14q10 10 20 0V24" fill="#e9a94d"/>'
    elif 'Radius' in label:body='<path d="M12 52V28Q12 12 30 12H52V52Z" fill="#b8cce2"/><path d="M12 28Q12 12 30 12" stroke="#e99427" stroke-width="6" fill="none"/>'
    elif 'Fase' in label:body='<path d="M12 52V28L28 12H52V52Z" fill="#b8cce2"/><path d="M12 28 28 12" stroke="#e99427" stroke-width="6"/>'
    elif 'Neig' in label:body='<path d="M10 52 25 12H45L54 52Z" fill="#b8cce2"/><path d="M10 52V12M10 42Q20 42 22 30" fill="none" stroke="#e99427" stroke-width="3"/>'
    elif 'Norm' in label:body='<path d="M18 10 46 10 60 32 46 54 18 54 4 32Z" fill="#b8cce2"/><circle cx="32" cy="32" r="12" fill="white"/>'
    elif 'Kant' in label or 'Mess' in label:body='<path d="M8 20H56M8 12V52M56 12V52M8 44H56M8 44l8-5m-8 5 8 5m40-5-8-5m8 5-8 5" fill="none"/><text x="22" y="36" font-size="15" fill="#185a9d" stroke="none">mm</text>'
    elif 'Maus' in label:body='<path d="M32 4V60M4 32H60M32 4l-6 8m6-8 6 8m-6 48-6-8m6 8 6-8M4 32l8-6m-8 6 8 6m48-6-8-6m8 6-8 6" fill="none" stroke="#185a9d" stroke-width="4"/>'
    elif 'Projekt' in label:body='<path d="M6 20V12H28L34 20H58V54H6Z" fill="#e9b85c"/>'
    elif any(word in label for word in ('Assistent','KI','Diktat')):body='<path d="m32 4 8 20 20 8-20 8-8 20-8-20-20-8 20-8Z" fill="#c0d8ef"/><path d="M48 6v12m-6-6h12" stroke="#e99427"/>'
    elif 'Zeich' in label or 'A4' in label:body='<path d="M12 4H44L54 14V60H12Z" fill="white"/><path d="M20 24H46M20 34H46M20 44H40" stroke="#185a9d"/>'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g stroke="#355576" stroke-width="2" stroke-linejoin="round">{body}</g></svg>'
    pix=QPixmap(64,64);pix.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pix);QSvgRenderer(QByteArray(svg.encode())).render(painter);painter.end()
    return QIcon(pix)
