"""Installed and imported placeables with lazy, local geometry previews."""
from pathlib import Path
from functools import lru_cache
import hashlib
import html
import struct
from .nwn.game_assets import GameAssets
from .model_preview import geometry,svg

class DiskGameAssets(GameAssets):
    def get(self,name,kind):
        path,index=self.index[name.lower(),kind]
        with path.open('rb') as stream:
            stream.seek(16);table=struct.unpack('<I',stream.read(4))[0]
            stream.seek(table+index*16);_,offset,size,actual=struct.unpack('<4I',stream.read(16))
            if actual!=kind:raise ValueError('Unexpected installed resource type')
            stream.seek(offset);raw=stream.read(size)
            if len(raw)!=size:raise ValueError('Truncated installed resource')
            return raw

@lru_cache(maxsize=4)
def installed(game_root):return DiskGameAssets(Path(game_root))

@lru_cache(maxsize=4)
def builtin_assets(game_root):
    from .custom_assets import table
    game=installed(game_root)
    if ('placeables',2017) not in game.index:return []
    raw=game.get('placeables',2017);digest=hashlib.sha256(raw).hexdigest()
    return [dict(id='builtin_ap'+str(i),name=row.get('Label') or ('Appearance '+str(i)),pack='builtin',sha256=digest,resref='',appearance=i,model=row['ModelName'].lower())
            for i,row in table(raw).items() if row.get('ModelName','****')!='****' and (row['ModelName'].lower(),2002) in game.index]

def model_bytes(library,asset):
    from .custom_assets import FileArchive
    model=asset['model']
    if not model:raise ValueError('This blueprint has no resolved model; import its appearance table')
    if asset['pack']!='builtin':
        archive=FileArchive(library.root/(asset['pack']+'.hak'))
        if (model,2002) in archive:return archive[model,2002]
        candidates=[]
        for pack in library.list()['packs']:
            if pack['pack']==asset['pack']:continue
            other=FileArchive(library.root/(pack['pack']+'.hak'))
            if (model,2002) in other:candidates.append(other[model,2002])
        if candidates:
            if len({hashlib.sha256(raw).digest() for raw in candidates})>1:raise ValueError('Multiple supporting packs provide different versions of this model; resolve pack priority before previewing')
            return candidates[0]
    if library.game_root:
        try:return installed(library.game_root).get(model,2002)
        except KeyError:pass
    raise ValueError('Model dependency missing from this pack and the installed game')

@lru_cache(maxsize=32)
def cached_geometry(raw):return geometry(raw)

def detail(library,ident):
    asset=next((a for a in library.list()['assets'] if a['id']==ident),None)
    if asset is None:raise ValueError('Unknown catalog asset')
    try:
        raw=model_bytes(library,asset);mesh=cached_geometry(raw)
        return dict(asset=asset,available=True,dimensions=mesh['dimensions'],bounds=mesh['bounds'],preview='static_mesh',notice='Actual static model geometry. Textures, effects and animations are omitted; model bounds are not collision bounds.'),mesh
    except (ValueError,KeyError,struct.error,IndexError,UnicodeError) as exc:
        return dict(asset=asset,available=False,dimensions=None,bounds=None,preview='unavailable',notice=str(exc)),None

def preview(library,ident,angle=35):
    if type(angle) is not int or not -180<=angle<=180:raise ValueError('Invalid preview angle')
    info,mesh=detail(library,ident)
    if mesh:return svg(mesh,info['asset']['name'],angle)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" fill="#18282c"/><text x="15" y="100" fill="white" font-size="13">Preview unavailable</text><text x="15" y="125" fill="#b0c1c5" font-size="10">'+html.escape(info['asset']['model'])+'</text></svg>').encode()

def visual_evidence(library,assets):
    """Bound image cost after retrieval; this is not a catalog/import limit."""
    import base64
    from .model_preview import contact_sheet
    images=[];labels=[];meshes=[]
    for asset in assets:
        try:mesh=cached_geometry(model_bytes(library,asset))
        except (ValueError,KeyError,struct.error,IndexError,UnicodeError):continue
        labels.append(dict(sheet=len(images)+1,cell=len(meshes)+1,id=asset['id'],dimensions=mesh['dimensions']))
        meshes.append(mesh)
        if len(meshes)==16:images.append('data:image/png;base64,'+base64.b64encode(contact_sheet(meshes)).decode());meshes=[]
        if len(images)==3:break
    if meshes:images.append('data:image/png;base64,'+base64.b64encode(contact_sheet(meshes)).decode())
    return labels,images
