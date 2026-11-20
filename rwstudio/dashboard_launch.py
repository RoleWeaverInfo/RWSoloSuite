"""Launch an exact exported build from the already-running local service."""
from pathlib import Path
import re
import subprocess
import sys
import time
import platform as host_platform

from . import launcher
from .builder import install_build
from .service import adventure_document


def executable(game_root, platform=None):
    platform = platform or sys.platform
    names = {'win32': ['bin/win32/nwmain.exe'],
             'darwin': ['bin/macos/nwmain.app/Contents/MacOS/nwmain', 'bin/macos/nwmain'],
             'linux': ['bin/linux-x86/nwmain-linux', 'bin/linux-x86/nwmain', 'bin/linux-x86_64/nwmain']}
    if platform.startswith('linux') and host_platform.machine().lower() in ('aarch64','arm64'):
        names['linux'] = ['bin/linux-arm64/nwmain-linux', 'bin/linux-arm64/nwmain'] + names['linux']
    for root in launcher.game_candidates(game_root):
        for name in names.get(platform, names['linux']):
            candidate = (root/name).resolve()
            if candidate.is_file():
                return candidate
    raise ValueError('NWN:EE was not found. Set the NWN installation folder in Local settings. On Linux, use the native NWN installation.')


def launch_build(app, build_id):
    # The HTTP caller holds BUILD_LOCK through installation and process startup.
    if launcher.game_running():
        raise ValueError('NWN is already running. Save and exit it before starting another build. To load a saved game, use NWN’s Load Game menu.')
    project = app.store.built_project(build_id)
    module = project['module_name']
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,15}', module):
        raise ValueError('Invalid module filename. Rebuild this adventure.')
    exe = executable(app.config['game_root'])
    user = Path(app.config['user_dir']).expanduser().resolve()
    if not user.is_dir():
        raise ValueError('Start NWN once, then check its user folder in Local settings.')
    # Check native build identity before installing or enabling the bridge.
    document = adventure_document(app.store.root/'builds'/build_id/(module+'.mod'))
    if document['build_id'] != build_id:
        raise ValueError('The native module belongs to a different build. Rebuild it first.')
    if project.get('ai_conversations') and not app.credentials.get(app.config['provider']):
        raise ValueError('Save an API key in Local settings before launching this AI-enabled adventure.')
    installed = install_build(app.store, build_id, user)
    app.store.register_player_build(build_id, document['project'])
    if project.get('ai_conversations'):
        from .server import database_path
        app.bridge.path = database_path(user)
        app.bridge.enabled = True
    # A frozen Python runtime must not inject its bundled libraries into NWN.
    from .updates import external_environment
    env = external_environment()
    log = app.store.root/'nwn-launch.log'
    with log.open('ab') as stream:
        child = subprocess.Popen([str(exe), '-userdirectory', str(user), '+LoadNewModule', module],
                                 cwd=exe.parent, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                 creationflags=launcher.NO_WINDOW)
    time.sleep(.7)
    if child.poll() is not None:
        raise ValueError('NWN exited during startup (code '+str(child.returncode)+'). Check Steam and the game installation. Details: '+str(log))
    return dict(started=True, module=module, pid=child.pid, **installed)
