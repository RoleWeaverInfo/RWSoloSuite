"""Build Python-included Linux/macOS packages on a matching native runner."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import package as release
from rwstudio import VERSION

ROOT=Path(__file__).resolve().parent

def main():
    if sys.platform not in ('linux','darwin'):raise SystemExit('Build on native Linux or macOS.')
    compiler=ROOT/'vendor/nwnsc/nwnsc'
    if not compiler.is_file():raise SystemExit('Run installer/build_nwnsc.py first.')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rw-native-') as temporary:
        stage=Path(temporary);source=release.package(output=stage)
        import zipfile
        with zipfile.ZipFile(source['package']) as archive:archive.extractall(stage)
        app=stage/'Role-Weaver-Module-Studio'
        (app/'vendor/nwnsc/nwnsc.exe').unlink(missing_ok=True)
        (app/'vendor/nwnsc/nwnsc').chmod(0o755)
        (app/'installation.json').write_text(json.dumps(dict(version=VERSION,data_mode='per-user')))
        datas=[(str(p),str(p.relative_to(app).parent)) for p in app.rglob('*') if p.is_file() and p.name!='nwnsc']
        spec=stage/'RoleWeaverModuleStudio.spec'
        content="""from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_submodules
datas = DATA_FILES
binaries = [(COMPILER, 'vendor/nwnsc')]
hiddenimports = collect_submodules('rwstudio')
for package in ('guardrails', 'litellm', 'tiktoken', 'jsonschema_specifications', 'keyring'):
    d, b, h = collect_all(package)
    datas += d; binaries += b; hiddenimports += h
for distribution in ('guardrails-ai', 'guardrails-ai-regex-match', 'keyring'):
    datas += copy_metadata(distribution, recursive=True)
a = Analysis([ENTRY], pathex=[APP_ROOT], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, excludes=['tkinter', 'IPython', 'pytest'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='RoleWeaverModuleStudio',
    console=True, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='RoleWeaverModuleStudio', strip=False, upx=False)
""".replace('DATA_FILES',repr(datas)).replace('COMPILER',repr(str(app/'vendor/nwnsc/nwnsc'))).replace('ENTRY',repr(str(ROOT/'installer/frozen_entry.py'))).replace('APP_ROOT',repr(str(app)))
        if sys.platform=='darwin':
            content+="\napp = BUNDLE(coll, name='Role Weaver Module Studio.app', bundle_identifier='com.roleweaver.modulestudio', info_plist={'CFBundleShortVersionString': '0.21.0', 'NSHighResolutionCapable': True})\n"
        spec.write_text(content)
        subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(stage/'frozen'),'--workpath',str(stage/'work'),str(spec)],check=True)
        if sys.platform=='darwin':
            bundle=stage/'frozen/Role Weaver Module Studio.app'
            executable=bundle/'Contents/MacOS/RoleWeaverModuleStudio'
        else:
            bundle=stage/'frozen/RoleWeaverModuleStudio';executable=bundle/'RoleWeaverModuleStudio'
        env=dict(os.environ,ROLEWEAVER_DATA_DIR=str(stage/'smoke-data'))
        subprocess.run([str(executable),'--self-test'],env=env,check=True,timeout=180)
        arch={'aarch64':'arm64','arm64':'arm64','x86_64':'x64'}[platform.machine().lower()]
        name=f'Role-Weaver-Module-Studio-{VERSION}-'+('macOS' if sys.platform=='darwin' else 'Linux')+'-'+arch
        if sys.platform=='darwin':
            # Verify the ad-hoc signature and preserve app symlinks in the archive.
            subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True)
            target=out/(name+'.zip')
            subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(bundle),str(target)],check=True)
        else:
            shutil.copytree(ROOT/'docs',bundle/'docs')
            target=out/(name+'.tar.gz')
            with tarfile.open(target,'w:gz') as archive:archive.add(bundle,arcname='RoleWeaverModuleStudio')
        digest=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
        target.with_name(target.name+'.sha256').write_text(digest+'  '+target.name+'\n')
        print(json.dumps(dict(package=str(target),architecture=arch,sha256=digest,smoke_test='passed',signed='ad-hoc' if sys.platform=='darwin' else False)))

if __name__=='__main__':main()
