import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from rwstudio.authoring import blank
from rwstudio.authoring_ai import generate
from rwstudio.custom_assets import AssetLibrary
from rwstudio.design_tools import regenerate_room

def asset(name,number):
    digest=str(number)*64;pack='rw'+digest[:14]
    return dict(id=pack+'_ap8000',name=name,pack=pack,sha256=digest,resref='',appearance=8000,model='plc_'+name.lower())

class AssetRetrievalTests(unittest.TestCase):
 def test_full_catalog_search_is_not_limited_to_browser_page(self):
  with tempfile.TemporaryDirectory() as tmp:
   library=AssetLibrary(Path(tmp));items=[dict(asset('Crate',1),id='crate_'+str(n)) for n in range(10050)]+[asset('Royal Throne',2)]
   with patch.object(library,'list',return_value={'packs':[],'assets':items}):
    self.assertEqual(library.search('royal throne')[0]['name'],'Royal Throne')
    self.assertEqual(library.search('nonexistent'),[])
 def test_generation_retrieves_optional_assets_and_retains_only_used_pack(self):
  with tempfile.TemporaryDirectory() as tmp:
   library=AssetLibrary(Path(tmp));throne=asset('Throne',1);crate=asset('Crate',2)
   p=blank();p['design_mode']='area';before=copy.deepcopy(p)
   generated=copy.deepcopy(p);generated['custom_placements']=[dict(id='chosen_throne',name='Royal throne',room='arrival',asset_id=throne['id'],placement='north',description='A focal point')]
   provider=Mock();provider.request.side_effect=[{'queries':['throne','crate']},generated]
   with patch.object(library,'list',return_value={'packs':[],'assets':[throne,crate]}):
    result=generate(provider,p,'A throne room','area','starting_area',asset_library=library)['proposal']
   self.assertEqual(result['custom_assets'],[throne]);self.assertEqual(p,before)
   context=provider.request.call_args_list[1].args[1]
   self.assertEqual(len(context['custom_asset_catalog']),2)
   self.assertEqual(result['custom_placements'][0]['asset_id'],throne['id'])
 def test_model_can_use_no_custom_objects(self):
  library=Mock();library.generation_candidates.return_value=[asset('Throne',1)]
  p=blank();p['design_mode']='area';generated=copy.deepcopy(p);generated['custom_placements']=[]
  provider=Mock();provider.request.return_value=generated
  result=generate(provider,p,'An empty hall','area','starting_area',asset_library=library)['proposal']
  self.assertEqual(result['custom_assets'],[]);self.assertEqual(result.get('custom_packs',[]),[])
 def test_room_regeneration_keeps_retrieved_asset_identity(self):
  p=blank();p['design_mode']='area';throne=asset('Throne',1);generated=copy.deepcopy(p)
  generated['custom_assets']=[throne];generated['custom_placements']=[dict(id='chosen_throne',name='Throne',room='arrival',asset_id=throne['id'],placement='north',description='')]
  with patch('rwstudio.authoring_ai.generate',return_value={'proposal':generated}):
   result=regenerate_room(Mock(),p,'arrival','Add a throne',asset_library=Mock())['proposal']
  self.assertEqual(result['custom_assets'],[throne]);self.assertEqual(len(result['custom_placements']),1)
 def test_empty_library_needs_no_selection_request(self):
  with tempfile.TemporaryDirectory() as tmp:
   provider=Mock();self.assertEqual(AssetLibrary(Path(tmp)).generation_candidates(provider,blank(),'Room','starting_area',[]),[]);provider.request.assert_not_called()
