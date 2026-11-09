"""Rebuild the supplied editable example (PYTHONPATH=src python examples/create_examples.py)."""
from pathlib import Path
from model import Part
from features import Feature,drilling_direction
from projects import save_project

plate=Part.create('Quader',(80,50,12));plate.name='Bohrplatte – bearbeitbar'
for x in (-28,28):
    for y in (-15,15):
        plate.add_feature(Feature('hole',((x,y,6),(0,0,-1),6.6,12,True,'counterbore',12,4,'')))
plate.add_feature(Feature('hole',((0,0,6),drilling_direction((0,0,1),25,0),8,8,False,'none',16,3,'')))
edges=tuple(i for i,e in enumerate(plate.shape.Edges()) if e.geomType()=='LINE' and abs(e.Length()-12)<1e-5 and abs(abs(e.Center().x)-40)<1e-5 and abs(abs(e.Center().y)-25)<1e-5)
assert len(edges)==4
plate.add_feature(Feature('fillet',(edges,3)))
save_project([plate],Path(__file__).with_name('Bohrplatte.pcad'))
