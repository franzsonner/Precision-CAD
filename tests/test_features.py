import math
import pytest
from model import Part,Document
from features import Feature,drilling_direction,catalogue,edge_measure,measure_points
from projects import save_project,load_project
from assistant_core import offline_command,proposal
from drawing import sheet_svg


def hole(point=(0,0,10),direction=(0,0,-1),diameter=10,depth=20,through=True,counter='none',head=16,head_depth=3):
    return Feature('hole',(point,direction,diameter,depth,through,counter,head,head_depth,''))


def test_through_blind_tilt_and_senkung():
    p=Part.create('Quader',(50,30,20));before=p.shape.Volume()
    p.add_feature(hole());assert p.shape.Volume()==pytest.approx(before-math.pi*25*20)
    p=Part.create('Quader',(50,30,20));p.add_feature(hole(depth=6,through=False))
    assert p.shape.Volume()==pytest.approx(before-math.pi*25*6)
    q=Part.create('Quader',(50,30,20));q.add_feature(hole(direction=drilling_direction((0,0,1),25,0)))
    assert q.shape.isValid() and q.shape.Volume()<p.shape.Volume()
    for counter,head_depth in [('counterbore',3),('countersink',90)]:
        r=Part.create('Quader',(50,30,20));r.add_feature(hole(counter=counter,head_depth=head_depth))
        assert r.shape.isValid() and r.shape.Volume()<before-math.pi*25*20


def test_fillet_chamfer_draft_and_rotate():
    for kind in ('fillet','chamfer'):
        p=Part.create('Quader',(50,30,20));p.add_feature(Feature(kind,((0,),2)))
        assert p.shape.isValid() and p.shape.Volume()<30000
    p=Part.create('Quader',(50,30,20))
    index=max(range(len(p.shape.Faces())),key=lambda i:p.shape.Faces()[i].Center().x)
    p.add_feature(Feature('draft',(index,2,5)))
    assert p.shape.isValid() and p.shape.Volume()<30000
    p.add_feature(Feature('rotate',(2,45)))
    assert p.shape.BoundingBox().xlen>50


def test_feature_resize_undo_failure_atomic_and_project(tmp_path):
    doc=Document();doc.add(Part.create('Quader',(50,30,20)))
    doc.position(0,(10,20,30));doc.feature(0,hole())
    doc.resize(0,(60,30,20))
    assert doc.parts[0].shape.Volume()==pytest.approx(36000-math.pi*25*20)
    assert doc.parts[0].position==(10,20,30)
    before=doc.parts[0].shape.Volume();n=len(doc.undo_stack)
    with pytest.raises(Exception):doc.feature(0,Feature('fillet',((0,),10000)))
    assert len(doc.undo_stack)==n and doc.parts[0].shape.Volume()==pytest.approx(before)
    path=tmp_path/'Bauteil.pcad';save_project(doc.parts,path)
    loaded=load_project(path)
    assert loaded[0].features[0].kind=='hole' and loaded[0].position==(10,20,30)
    loaded[0].resize((70,30,20))
    assert loaded[0].shape.Volume()==pytest.approx(42000-math.pi*25*20)
    doc.undo();assert doc.parts[0].dimensions==(50,30,20)
    doc.redo();assert doc.parts[0].dimensions==(60,30,20)


def test_imported_project_and_boolean(tmp_path):
    doc=Document();doc.add(Part.create('Quader',(50,30,20)));doc.add(Part.create('Zylinder',(5,1,20)))
    doc.position(1,(0,0,-10));doc.combine([0,1],cut=True)
    p=doc.parts[0]
    assert p.shape.Volume()==pytest.approx(30000-math.pi*25*20)
    p.add_feature(Feature('rotate',(0,15)));p.set_position((2,3,4))
    path=tmp_path/'imported.pcad';save_project(doc.parts,path);loaded=load_project(path)
    assert loaded[0].shape.Volume()==pytest.approx(p.shape.Volume())
    assert loaded[0].shape.BoundingBox().zmax==pytest.approx(p.shape.BoundingBox().zmax)
    doc.undo();assert len(doc.parts)==2
    doc.redo();assert len(doc.parts)==1


@pytest.mark.parametrize('kind',['bolt','nut','washer'])
def test_catalogue(kind):
    name,shape=catalogue(kind,10,30,1)
    assert shape.isValid() and shape.Volume()>0 and 'M10' in name
    if kind=='bolt':assert shape.BoundingBox().zlen==pytest.approx(36.4)


def test_measurement_and_drawing():
    p=Part.create('Quader',(50,30,20));edges=p.shape.Edges()
    pairs=[(i,j) for i,a in enumerate(edges) for j,b in enumerate(edges) if i<j and abs(a.distance(b)-50)<1e-5]
    assert pairs
    a,b=pairs[0];value,angle,u,v=measure_points(p.shape,a,b)
    assert value==pytest.approx(50) and math.dist(u,v)==pytest.approx(value)
    doc=Document();doc.add(p);doc.measure(0,a,b)
    svg=sheet_svg(doc.parts[0]);assert '3D-Kantenabstand: 50.000 mm' in svg and 'data-axis="0"' in svg
    doc.resize(0,(60,30,20));assert not doc.parts[0].measurements


def test_offline_assistant_preview_does_not_change_model():
    p,row=proposal(offline_command('Quader 80 40 20'),[])
    assert row is None and p.shape.Volume()==pytest.approx(64000)
    changed,row=proposal(offline_command('Bohrung 8'),[p],0)
    assert changed.shape.Volume()<p.shape.Volume() and not p.features
    with pytest.raises(ValueError):offline_command('Führe Python aus')
    with pytest.raises(ValueError):proposal({'command':'box','x':float('inf'),'y':1,'z':1},[])


def test_top_face_draft_and_native_measurements(tmp_path):
    doc=Document();doc.add(Part.create('Quader',(50,30,20)))
    face=max(range(len(doc.parts[0].shape.Faces())),key=lambda i:doc.parts[0].shape.Faces()[i].Center().z)
    doc.feature(0,Feature('draft',(face,0,5)))
    assert doc.parts[0].shape.isValid() and doc.parts[0].shape.Volume()<30000
    doc.measure(0,0)
    path=tmp_path/'neigung.pcad';save_project(doc.parts,path)
    loaded=load_project(path)
    assert loaded[0].measurements==((0,None),)
    assert 'Flächenneigung' in sheet_svg(loaded[0])


def test_ai_transport_is_structured_and_never_executes(monkeypatch):
    import io,json,assistant_core
    result={'command':'box','x':80,'y':40,'z':20,'diameter':0,'depth':20,'angle':0,'radius':0,'axis':2,'through':True}
    captured={}
    def respond(request,timeout):
        captured['url']=request.full_url;captured['data']=json.loads(request.data)
        return io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps(result)}}]}).encode())
    monkeypatch.setattr(assistant_core,'urlopen',respond)
    command=assistant_core.ai_command('Erstelle einen Quader 80 mal 40 mal 20','test-key')
    assert captured['url']=='https://api.openai.com/v1/chat/completions'
    assert captured['data']['response_format']['json_schema']['strict']
    assert captured['data']['messages'][1]['content']=='Erstelle einen Quader 80 mal 40 mal 20'
    part,_=proposal(command,[])
    assert part.shape.Volume()==pytest.approx(64000)
    result['command']='execute_python'
    with pytest.raises(ValueError):assistant_core.ai_command('Befehl','test-key')


def test_meshing_does_not_change_drawing_dimensions():
    from features import exact_box
    from drawing import editable_axis
    p=Part.create('Quader',(50,30,20));p.add_feature(Feature('fillet',((0,),1.5)))
    p.shape.tessellate(.15)
    assert exact_box(p.shape).xlen==pytest.approx(50)
    assert editable_axis(p,0)


def test_edit_existing_hole_and_remove_following_steps():
    doc=Document();doc.add(Part.create('Quader',(50,30,20)))
    doc.feature(0,hole(diameter=6));doc.feature(0,Feature('rotate',(2,10)))
    doc.change_feature(0,0,hole(diameter=10))
    assert len(doc.parts[0].features)==2
    assert doc.parts[0].shape.Volume()==pytest.approx(30000-math.pi*25*20)
    doc.truncate_features(0,0);assert not doc.parts[0].features
    assert doc.parts[0].shape.Volume()==pytest.approx(30000)
    doc.undo();assert len(doc.parts[0].features)==2


def test_topology_changes_cannot_silently_retarget_a_fillet():
    doc=Document();doc.add(Part.create('Quader',(50,30,20)))
    doc.feature(0,hole(diameter=6));doc.feature(0,Feature('fillet',((0,),1)))
    before=doc.parts[0].shape.Volume()
    with pytest.raises(ValueError,match='Kantenstruktur'):
        doc.change_feature(0,0,hole(point=(25,0,10),diameter=6))
    assert doc.parts[0].shape.Volume()==pytest.approx(before)


def test_inclined_hole_has_complete_elliptical_opening_not_a_clipped_cap():
    p=Part.create('Quader',(60,60,20));tilt=30
    p.add_feature(hole(direction=drilling_direction((0,0,1),tilt,0)))
    expected=math.pi*25/math.cos(math.radians(tilt))
    top=max((f for f in p.shape.Faces() if f.geomType()=='PLANE'),key=lambda f:f.Center().z)
    assert top.Area()==pytest.approx(3600-expected)
    assert p.shape.Volume()==pytest.approx(72000-expected*20)
