"""Read installed NWN KEY/BIF resources without modifying the game."""
from pathlib import Path
import struct


class GameAssets:
    def __init__(self, root):
        self.root = Path(root)
        self.index = {}
        self.bifs = {}
        for key in (self.root / 'data' / 'nwn_base.key', self.root / 'data' / 'nwn_retail.key'):
            if not key.exists():
                continue
            raw = key.read_bytes()
            assert raw[:8] == b'KEY V1  '
            nf, nk, fo, ko = struct.unpack_from('<4I', raw, 8)
            files = []
            for i in range(nf):
                _, off, size, _ = struct.unpack_from('<IIHH', raw, fo + 12*i)
                name = raw[off:off+size].rstrip(b'\0').decode().replace('\\', '/')
                path = self.root / name
                if not path.exists():
                    path = key.parent / Path(name).name
                files.append(path)
            for i in range(nk):
                name, kind, ident = struct.unpack_from('<16sHI', raw, ko + 22*i)
                self.index[name.rstrip(b'\0').decode().lower(), kind] = (files[ident >> 20], ident & 0xFFFFF)

    def get(self, name, kind):
        path, index = self.index[name.lower(), kind]
        if path not in self.bifs:
            self.bifs[path] = path.read_bytes()
        raw = self.bifs[path]
        table = struct.unpack_from('<I', raw, 16)[0]
        _, offset, size, actual = struct.unpack_from('<4I', raw, table + index*16)
        assert actual == kind
        return raw[offset:offset+size]


if __name__ == '__main__':
    import sys
    from gff import read
    game = GameAssets(sys.argv[1])
    for kind in (2027, 2025, 2042, 2029, 2030):
        names = sorted(n for n,k in game.index if k == kind)
        print(kind, len(names), [n for n in names if any(s in n for s in ('gob','common','cit','chest','heal','bag','guard','rat'))][:70])
    for name, kind in [('nw_c2_default9',2009), ('nw_goblin',2027)]:
        if (name,kind) in game.index:
            print(name, 'present')
