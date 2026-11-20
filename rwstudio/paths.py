"""Keep packaged application files separate from each user's workspace."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def default_data(root=None):
    root = Path(root) if root is not None else ROOT
    override = os.environ.get('ROLEWEAVER_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if (root/'installation.json').is_file() or getattr(sys,'frozen',False):
        if sys.platform=='darwin':return Path.home()/'Library/Application Support/RoleWeaver/ModuleStudio'
        if sys.platform!='win32':return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'RoleWeaver/ModuleStudio'
        local = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData/Local')
        return local/'RoleWeaver'/'ModuleStudio'
    return root/'data'


def nwn_user_dir():
    if sys.platform.startswith('linux'):
        return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'Neverwinter Nights'
    return Path.home()/'Documents/Neverwinter Nights'


def compiler_path(root=ROOT):
    return Path(root)/'vendor/nwnsc'/('nwnsc.exe' if sys.platform=='win32' else 'nwnsc')
