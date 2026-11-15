"""Independent physical doorway checks using installed stock walkmeshes."""
import json
import configparser
import math
import unittest
from pathlib import Path
from rwstudio.nwn.game_assets import GameAssets
from rwstudio.nwn.area_tools import node
from rwstudio.layout import plan,native_tiles
from rwstudio.companion_tasks import example

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')

def triangles(raw,walkable):
 lines=[s.strip().split() for s in raw.decode('latin1').splitlines() if s.strip()]
 offset=(0,0,0);vertices=[];out=[]
 for i,t in enumerate(lines):
  if t[0]=='position':offset=tuple(map(float,t[1:4]))
  if t[0]=='verts':vertices=[tuple(float(v)+offset[j] for j,v in enumerate(row[:3])) for row in lines[i+1:i+1+int(t[1])]]
  if t[0]=='faces':
   for row in lines[i+1:i+1+int(t[1])]:
    if int(row[-1]) in walkable:out.append([vertices[int(n)] for n in row[:3]])
 return out

def contains(triangle,x,y):
 a,b,c=triangle
 cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
 sub=lambda u,v:(u[0]-v[0],u[1]-v[1])
 det=cross(sub(b,a),sub(c,a))
 if abs(det)<1e-7:return False
 u=cross(sub((x,y),a),sub(c,a))/det;v=cross(sub(b,a),sub((x,y),a))/det
 return u>=-1e-4 and v>=-1e-4 and u+v<=1.0001

@unittest.skipUnless(GAME.is_dir(),'Installed NWN stock resources required')
class PhysicalDoorwayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.assets=GameAssets(GAME);cls.meshes={};cls.configs={}
  rows=[line.split() for line in cls.assets.get('surfacemat',2017).decode('latin1').splitlines()]
  cls.walkable={int(row[0]) for row in rows if row and row[0].isdigit() and row[2]=='1'}
 def test_every_interior_room_endpoint_has_an_open_walkmesh_across_its_door(self):
  p=json.loads((Path(__file__).resolve().parents[1]/'examples/companion_upgrade.rwproject.json').read_text(encoding='utf8'));layouts=plan(p)
  template=node(0,Tile_ID=(4,0),Tile_Orientation=(4,0),Tile_Height=(4,0))
  total=0
  for area in p['areas']:
   layout=layouts[area['id']];tiles=native_tiles(template,area,layout)
   cfg=configparser.ConfigParser(strict=False);cfg.read_string(self.assets.get(layout['tileset'],2013).decode('latin1'))
   for opening in layout['doorways']:
    total+=1;dx,dy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[opening['side']]
    # Walk through both doorway tiles, with clearance on either side of centre.
    for n in range(-19,20):
     for lateral in (-.4,0,.4):
      x=opening['x']+dx*n*.5-dy*lateral;y=opening['y']+dy*n*.5+dx*lateral
      tx=int(x//10);ty=int(y//10);t=tiles[ty*area['width']+tx][1]
      model=cfg['TILE'+str(t['Tile_ID'][1])]['model'].lower()
      if model not in self.meshes:self.meshes[model]=triangles(self.assets.get(model,2016),self.walkable)
      angle=-t['Tile_Orientation'][1]*math.pi/2;lx=x-tx*10-5;ly=y-ty*10-5
      mx=lx*math.cos(angle)-ly*math.sin(angle);my=lx*math.sin(angle)+ly*math.cos(angle)
      self.assertTrue(any(contains(tri,mx,my) for tri in self.meshes[model]),(area['id'],opening['room'],opening['side'],model,x,y))
   expected=sum(2 for c in p['connections'] if c['kind']=='corridor' and any(r['id']==c['from_room'] for r in area['rooms'])) if area['type']!='forest' else 0
   self.assertEqual(len(layout['doorways']),expected)
  self.assertGreater(total,0)

 def test_supported_stock_models_have_openings_and_solid_walls_beside_them(self):
  for model in ('tic01_d13_01','tde01_a13_01','tdm01_a13_01'):
   mesh=triangles(self.assets.get(model,2016),self.walkable)
   for x in (-4.,0.,3.,4.5,4.9):
    for y in (-.4,0.,.4):self.assertTrue(any(contains(tri,x,y) for tri in mesh),(model,x,y))
   self.assertFalse(any(contains(tri,4.9,3.0) for tri in mesh),model)
