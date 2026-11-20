"""Build the pinned NWScript compiler on the release's native architecture."""
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
REVISION='531b02eeba96b081637b1427a306c8332798fc13'

def run(*args,**kwargs):subprocess.run(args,check=True,**kwargs)

def main():
    source=ROOT/'data/native-compiler/source';build=source.parent/'build'
    if not source.exists():
        source.parent.mkdir(parents=True,exist_ok=True)
        run('git','clone','https://github.com/nwneetools/nwnsc.git',str(source))
    run('git','checkout','--detach',REVISION,cwd=source)
    if sys.platform=='darwin':
        cmake=source/'CMakeLists.txt';text=cmake.read_text()
        text=text.replace('set(CMAKE_OSX_ARCHITECTURES arm64;x86_64)','set(CMAKE_OSX_ARCHITECTURES '+platform.machine()+')')
        cmake.write_text(text)
    run('cmake','-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=OFF')
    run('cmake','--build',str(build),'--parallel','3')
    binary=next(p for p in build.rglob('nwnsc') if p.is_file())
    target=ROOT/'vendor/nwnsc/nwnsc';shutil.copy2(binary,target);target.chmod(0o755)
    print('Native compiler:',platform.machine(),REVISION)

if __name__=='__main__':main()
