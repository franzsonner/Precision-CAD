"""Constrained CAD commands; optional AI returns JSON, never executable code."""
from dataclasses import replace
import json
import math
import re
from urllib.request import Request,urlopen
from features import Feature,drilling_direction
from model import Part

COMMANDS=('box','cylinder','hole','fillet','chamfer','rotate','move')
NUMBERS=('x','y','z','diameter','depth','angle','radius','axis')


def validate(command):
    if command.get('command') not in COMMANDS:
        raise ValueError('Dieser Befehl wird nicht unterstützt.')
    for field in NUMBERS:
        value=command.get(field,0)
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>100000:
            raise ValueError(f'Ungültiger Befehlswert: {field}')
    if command.get('axis',0) not in (0,1,2):raise ValueError('Achse muss X, Y oder Z sein.')
    return command


def offline_command(text):
    text=text.lower().replace(',','.')
    values=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',text)]
    result={'x':0,'y':0,'z':0,'diameter':0,'depth':20,'angle':0,'radius':0,'axis':2,'through':True}
    if 'quader' in text and len(values)==3:result.update(command='box',x=values[0],y=values[1],z=values[2])
    elif 'zylinder' in text and len(values)==2:result.update(command='cylinder',radius=values[0],z=values[1])
    elif ('bohrung' in text or 'bohren' in text) and 1<=len(values)<=3:
        result.update(command='hole',diameter=values[0],through=len(values)==1,depth=values[1] if len(values)>1 else 20,angle=values[2] if len(values)>2 else 0)
    elif 'verschieb' in text and len(values)==3:result.update(command='move',x=values[0],y=values[1],z=values[2])
    elif 'radius' in text and len(values)==1:result.update(command='fillet',radius=values[0])
    elif 'fase' in text and len(values)==1:result.update(command='chamfer',radius=values[0])
    elif 'dreh' in text and len(values)==1:result.update(command='rotate',axis=0 if ' x' in text else 1 if ' y' in text else 2,angle=values[0])
    else:raise ValueError('Offline-Beispiele: Quader 80 40 20; Zylinder 10 30 (Radius/Höhe); Bohrung 8; Bohrung 8 15 30 (Durchmesser/Tiefe/Neigung); Radius 2; Fase 1; Verschieben 10 0 0; Drehen Z 45.')
    return validate(result)


def ai_command(text,key):
    if not key.strip():raise ValueError('Eigenen OpenAI-API-Schlüssel eingeben oder Offline-Modus nutzen.')
    properties={'command':{'type':'string','enum':list(COMMANDS)},'through':{'type':'boolean'}}
    properties.update({field:{'type':'number'} for field in NUMBERS})
    schema={'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    system=('Translate the German CAD instruction into exactly one supported command. Millimetres and degrees. '
            'box: x,y,z dimensions; cylinder: radius,z height; hole: diameter,depth,through,angle tilt 0..85; '
            'fillet/chamfer: radius for preselected edges; rotate: axis 0 X/1 Y/2 Z,angle; move: x,y,z displacement. '
            'Default numbers 0, depth 20, axis 2, through true. No code. Hole uses preselected planar face or top face. '
            'Do not invent unsupported geometry. If the instruction is outside these functions, set command box and x,y,z to 0 so validation rejects it.')
    body={'model':'gpt-4.1-mini','messages':[{'role':'system','content':system},{'role':'user','content':text}],
          'response_format':{'type':'json_schema','json_schema':{'name':'cad_command','strict':True,'schema':schema}},'max_tokens':500}
    request=Request('https://api.openai.com/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key.strip()},method='POST')
    try:
        with urlopen(request,timeout=60) as response:data=json.loads(response.read(1024*1024))
    except Exception:
        raise ValueError('KI-Anfrage fehlgeschlagen. API-Schlüssel, Guthaben und Internetverbindung prüfen.') from None
    return validate(json.loads(data['choices'][0]['message']['content']))


def proposal(command,parts,row=None,face_index=None,point=None,edge_indices=()):
    command=validate(command);kind=command['command']
    if kind=='box':return Part.create('Quader',(command['x'],command['y'],command['z'])),None
    if kind=='cylinder':return Part.create('Zylinder',(command['radius'],1,command['z'])),None
    if row is None or not 0<=row<len(parts):raise ValueError('Zuerst ein Bauteil auswählen.')
    part=replace(parts[row])
    if kind=='move':part.set_position(tuple(a+command.get(b,0) for a,b in zip(part.position,('x','y','z'))))
    elif kind=='rotate':part.add_feature(Feature('rotate',(int(command['axis']),command['angle'])))
    elif kind in ('fillet','chamfer'):
        if not edge_indices:raise ValueError('Zuerst Kanten auswählen.')
        part.add_feature(Feature(kind,(tuple(edge_indices),command['radius'])))
    elif kind=='hole':
        faces=part.shape.Faces()
        if face_index is None:
            indices=[i for i,f in enumerate(faces) if f.geomType()=='PLANE']
            if not indices:raise ValueError('Ebene Startfläche fehlt.')
            face_index=max(indices,key=lambda i:faces[i].Center().z)
            point=faces[face_index].Center().toTuple()
        face=faces[face_index]
        if face.geomType()!='PLANE':raise ValueError('Ebene Fläche wählen.')
        point=face.Center().toTuple() if point is None else point
        local=tuple(a-b for a,b in zip(point,part.position))
        direction=drilling_direction(face.normalAt().toTuple(),command.get('angle',0),0)
        part.add_feature(Feature('hole',(local,direction,command['diameter'],command.get('depth',20),command.get('through',True),'none',16,3,'')))
    return part,row
