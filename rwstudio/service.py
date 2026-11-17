"""Service-only startup and optional registration/installation of a shared adventure."""
import argparse
import re
import sys
import webbrowser
import json
from pathlib import Path
from . import launcher
from . import VERSION
from .content import validate_project
from .paths import default_data

ROOT = Path(__file__).resolve().parents[1]


def adventure_document(module):
    module = Path(module).expanduser().resolve()
    if module.suffix.lower() != '.mod' or not module.is_file():
        raise ValueError('Choose the .mod from the extracted adventure ZIP.')
    sidecar = module.with_suffix('.rwproject.json')
    if not sidecar.is_file():
        raise ValueError('Keep the matching .rwproject.json beside the .mod. Extract the complete adventure ZIP.')
    document = launcher.read_json(sidecar)
    project = validate_project(document.get('project', {}))
    build = document.get('build_id', '')
    if not isinstance(build, str) or not re.fullmatch(r'[0-9a-f]{20}', build) or project['module_name'] != module.stem:
        raise ValueError('The adventure profile does not match this module.')
    context = launcher.native_context(module)
    if context != dict(build_id=build, project_id=project['id']) and (context or project.get('ai_conversations')):
        raise ValueError('The adventure profile belongs to a different module build. Extract its matching ZIP.')
    return dict(build_id=build, project=project)


def install_adventure(module, user_dir):
    module = Path(module).resolve()
    user = Path(user_dir).expanduser().resolve()
    if not user.is_dir():
        raise ValueError('Start NWN once to create its user folder, then check the NWN user folder in Studio Settings.')
    # Dependencies can change even when the MOD is unchanged. Never replace any
    # part of a shared adventure while the engine may have those files open.
    if launcher.game_running():
        raise ValueError('Exit NWN before installing an adventure. Start Role Weaver first, then open NWN separately.')
    launcher.install(dict(source=str(module), installed=str(user/'modules'/module.name), user_dir=str(user)))


def startup_url(player=False, port=8766):
    return f'http://127.0.0.1:{port}/startup' + ('?view=player' if player else '')


def reuse(existing, module=None, player=False, open_browser=True):
    version = tuple(int(n) for n in re.findall(r'\d+', str(existing.get('version', '')))[:3])
    if version < (0, 20, 0) or existing.get('version') != VERSION:
        raise ValueError('An older or different Role Weaver version is running. Close its service window, then start this release again.')
    if module:
        document = adventure_document(module)
        launcher.http('/api/player/register', document, existing['csrf'])
        install_adventure(module, existing['settings']['user_dir'])
    launcher.http('/api/bridge', dict(enabled=True), existing['csrf'])
    if open_browser:
        webbrowser.open(startup_url(player))
    print('Role Weaver service is already running. Open NWN separately when ready.', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adventure', type=Path)
    parser.add_argument('--data', type=Path, default=default_data())
    parser.add_argument('--player', action='store_true')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--runtime-info', action='store_true', help='Print local runtime paths without starting the service')
    args = parser.parse_args(argv)
    if args.runtime_info:
        print(json.dumps(dict(version=VERSION,python=sys.version.split()[0],executable=sys.executable,application=str(ROOT),data=str(args.data)),indent=2))
        return
    try:
        existing = launcher.state()
        if existing:
            reuse(existing, args.adventure, args.player, not args.no_browser)
            return
        from .server import serve
        serve(args.data, open_browser=not args.no_browser, player=args.player, adventure=args.adventure)
    except KeyboardInterrupt:
        print('Role Weaver service stopped. NWN is managed separately.')
    except (OSError, ValueError, KeyError) as error:
        print('Cannot start Role Weaver: '+str(error), file=sys.stderr)
        raise SystemExit(1)
