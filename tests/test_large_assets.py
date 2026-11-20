import hashlib
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.custom_assets import AssetLibrary,FileArchive,archive,file_digest,write_loose_pack
from rwstudio.nwn.area_tools import pack_module
from rwstudio.builder import ROOT

class LargeAssetTests(unittest.TestCase):
 def test_disk_index_matches_archive_and_scan_avoids_read_bytes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'pack.hak'
   raw=b'HAK V1.0'+pack_module((ROOT/'assets/authoring-template.erf').read_bytes(),{('placeables',2017):b'2DA V2.0\n\nLabel ModelName\n8000 Test_Table plc_test\n',('plc_test',2002):b'test model'})[8:];source.write_bytes(raw)
   self.assertEqual(dict(FileArchive(source)),archive(raw))
   library=AssetLibrary(root/'studio')
   with patch.object(Path,'read_bytes',side_effect=AssertionError('Whole-file read is forbidden')):
    scanned=library.scan(source)
    self.assertEqual(scanned['assets'][0]['appearance'],8000)
    self.assertEqual(file_digest(source),hashlib.sha256(raw).hexdigest())
 def test_loose_resources_stream_to_pack(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);model=root/'chair.mdl';model.write_bytes(b'model data');out=root/'loose.hak'
   with patch.object(Path,'read_bytes',side_effect=AssertionError('Whole-file read is forbidden')):write_loose_pack(out,{('chair',2002):model})
   self.assertEqual(FileArchive(out)['chair',2002],b'model data')
 def test_import_accepts_hak_larger_than_old_512mb_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   if shutil.disk_usage(root).free<1_500_000_000:self.skipTest('Large import regression needs temporary disk space')
   path=root/'large.hak';raw=b'HAK V1.0'+pack_module((ROOT/'assets/authoring-template.erf').read_bytes(),{('placeables',2017):b'2DA V2.0\n\nLabel ModelName\n8000 Large_Test plc_large\n'})[8:]
   with path.open('wb') as f:f.write(raw);f.truncate(513_000_000)
   library=AssetLibrary(root/'studio');result=library.scan(path)
   self.assertEqual(result['packs'][0]['bytes'],513_000_000)
   self.assertEqual(result['assets'][0]['name'],'Large_Test')
   self.assertEqual((library.root/(result['added'][0]+'.hak')).stat().st_size,513_000_000)
 def test_bad_file_index_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'bad.hak';raw=bytearray(160);raw[:8]=b'HAK V1.0';struct.pack_into('<4I',raw,16,1,160,999999,999999);path.write_bytes(raw)
   with self.assertRaises(ValueError):FileArchive(path)
