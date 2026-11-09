"""A4 overview sheet: orthographic geometry and overall dimensions in mm."""
import xml.etree.ElementTree as ET
import math
from features import measure_points, exact_box
from cadquery.occ_impl.exporters.svg import getSVG

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def editable_axis(part,axis):
    if part.kind not in ('Quader','Zylinder') or any(f.kind in ('rotate','draft') for f in part.features):return False
    bb=exact_box(part.shape)
    expected=part.dimensions[axis] if part.kind=='Quader' or axis==2 else 2*part.dimensions[0]
    return abs((bb.xlen,bb.ylen,bb.zlen)[axis]-expected)<1e-4


def sheet_svg(part):
    root = ET.Element(f'{{{NS}}}svg', {'width': '297mm', 'height': '210mm', 'viewBox': '0 0 1122 794'})
    def text(x, y, value, size=16, axis=None, color="#172334", middle=False):
        node = ET.SubElement(root, f'{{{NS}}}text', {'x': str(x), 'y': str(y), 'font-size': str(size), 'font-family': 'Arial, sans-serif', 'fill': color, 'text-anchor':'middle' if middle else 'start'})
        if axis is not None and editable_axis(part,axis):
            node.set('data-axis',str(axis));node.set('fill','#176bb0');node.set('text-decoration','underline')
        node.text = value
    ET.SubElement(root, f'{{{NS}}}rect', {'x': '20', 'y': '20', 'width': '1082', 'height': '754', 'fill': 'white', 'stroke': '#172334'})
    text(40, 55, f'Precision CAD – {part.name}', 23)
    text(40, 84, 'Orthogonale Ansichten · Maße in mm · Blaue Grundmaße in der Vorschau anklicken')
    bb=exact_box(part.shape)
    projections=[]
    def line(x1,y1,x2,y2,color='#176bb0',dash=False):
        attrs={'x1':str(x1),'y1':str(y1),'x2':str(x2),'y2':str(y2),'stroke':color,'stroke-width':'1.1'}
        if dash:attrs['stroke-dasharray']='4 3'
        ET.SubElement(root,f'{{{NS}}}line',attrs)
    def dimension(p,q,label,axis=None,color='#176bb0'):
        x1,y1=p;x2,y2=q
        line(x1,y1,x2,y2,color)
        length=math.hypot(x2-x1,y2-y1)
        if length>1:
            ux,uy=(x2-x1)/length,(y2-y1)/length
            for x,y,sign in [(x1,y1,1),(x2,y2,-1)]:
                for side in [-1,1]:line(x,y,x+sign*ux*7-side*uy*3,y+sign*uy*7+side*ux*3,color)
        text((x1+x2)/2,(y1+y2)/2-6,label,13,axis,color,True)
    # OCCT hidden-line removal provides true parallel projections, also for STEP.
    views = [('Vorne (Blick entlang −Y)', (0, -1, 0), 50, 135),
             ('Rechts (Blick entlang −X)', (1, 0, 0), 595, 135),
             ('Oben (Blick entlang −Z)', (0, 0, 1), 50, 425)]
    for label, direction, x, y in views:
        text(x, y - 12, label)
        # OCCT chooses a rotated default X axis for the front/side projector.
        # Rotate the input around the viewing axis so Z stays vertical on paper.
        shape = part.shape
        if direction == (0, -1, 0):
            shape = shape.rotate((0, 0, 0), (0, 1, 0), 90)
        elif direction == (1, 0, 0):
            shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)
        svg = ET.fromstring(getSVG(shape, {
            'width': 450, 'height': 240, 'marginLeft': 45, 'marginTop': 25,
            'projectionDir': direction, 'showAxes': False, 'showHidden': True,
            'strokeColor': (20, 30, 40), 'hiddenColor': (130, 130, 130),
        }))
        group = ET.SubElement(root, f'{{{NS}}}g', {'transform': f'translate({x},{y})', 'data-view': label})
        group.extend(list(svg))
        ua,va=(0,2) if direction==(0,-1,0) else (1,2) if direction==(1,0,0) else (0,1)
        lengths=(bb.xlen,bb.ylen,bb.zlen);mins=(bb.xmin,bb.ymin,bb.zmin);maxs=(bb.xmax,bb.ymax,bb.zmax)
        scale=min(450/max(lengths[ua],1e-9)*.75,240/max(lengths[va],1e-9)*.75)
        def project(point,ua=ua,va=va,x=x,y=y,scale=scale,mins=mins,maxs=maxs):
            return x+45+(point[ua]-mins[ua])*scale,y+25+(maxs[va]-point[va])*scale
        projections.append(project)
        for edge_index,edge in enumerate(part.shape.Edges()):
            samples,_=edge.sample(2 if edge.geomType()=='LINE' else 48)
            points=[project(p.toTuple()) for p in samples]
            ET.SubElement(root,f'{{{NS}}}polyline',{'points':' '.join(f'{a:.5f},{b:.5f}' for a,b in points),
                'stroke':'none','fill':'none','data-edge':str(edge_index),'data-projection':str(len(projections)-1)})
        left,top=x+45,y+25;right,bottom=left+lengths[ua]*scale,top+lengths[va]*scale
        line(left,bottom,left,bottom+22);line(right,bottom,right,bottom+22)
        dimension((left,bottom+18),(right,bottom+18),f'{lengths[ua]:.3f}',ua)
        if direction==(0,-1,0):
            line(left,top,left-25,top);line(left,bottom,left-25,bottom)
            dimension((left-20,top),(left-20,bottom),f'{lengths[va]:.3f}',va)
    bb = exact_box(part.shape)
    text(595, 445, 'Gesamtabmessungen (achsenparalleler Hüllkörper)', 17)
    for index, (label, value) in enumerate([('X / Länge', bb.xlen), ('Y / Breite', bb.ylen), ('Z / Höhe', bb.zlen)]):
        if part.kind=='Zylinder' and index==0:label='Durchmesser'
        text(595, 475 + index * 24, f'{label}: {value:.3f} mm',axis=index)
    notes=[]
    for feature in part.features[-4:]:
        if feature.kind=='hole':
            args=feature.args
            notes.append(f'Bohrung ⌀{args[2]:g} – '+('durchgehend' if args[4] else f'Tiefe {args[3]:g}')+(f' | {args[8]} (Kennzeichnung)' if args[8] else ''))
        elif feature.kind in ('fillet','chamfer'):notes.append(f'{"Radius" if feature.kind=="fillet" else "Fase"}: {feature.args[1]:g} mm')
        elif feature.kind in ('rotate','draft'):notes.append(f'{"Drehung" if feature.kind=="rotate" else "Flächenneigung"}: {feature.args[-1]:g}°')
    text(595,555,'Bearbeitungen und ausgewählte Messwerte',15)
    for i,note in enumerate(notes):text(595,575+i*15,note,12)
    for i,record in enumerate(part.measurements):
        try:
            first,second=record
            value,angle,p,q=measure_points(part.shape,first,second)
            label=f'{"Kantenlänge" if second is None else "3D-Kantenabstand"}: {value:.3f} mm'
            if angle is not None:label+=f' / {angle:.3f}°'
            axis=None
            if part.kind=='Quader' and second is not None:
                diffs=[abs(a-b) for a,b in zip(p,q)];candidate=max(range(3),key=lambda j:diffs[j])
                if abs(value-part.dimensions[candidate])<1e-4 and sum(diffs)-diffs[candidate]<1e-4:axis=candidate
            text(595,575+(len(notes)+i)*15,label,12,axis,'#a83c64')
            if second is not None or part.shape.Edges()[first].geomType()=='LINE':
                projected=[(project(p),project(q)) for project in projections]
                a,b=max(projected,key=lambda pair:math.dist(*pair))
                dimension(a,b,f'{value:.3f}',axis,'#a83c64')
        except (ValueError,IndexError):
            continue
    text(40, 712, 'Ansichten einzeln eingepasst · Maßstab variabel · Nicht vom Ausdruck abmessen', 14)
    text(40, 739, 'Testversion: keine normgerechte Fertigungszeichnung; Toleranzen, Schnitte und Passungen fehlen.', 14)
    return ET.tostring(root, encoding='unicode')
