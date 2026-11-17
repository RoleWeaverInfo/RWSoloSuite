"""Keep installed application files separate from each Windows user's workspace."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def default_data(root=None):
    root = Path(root) if root is not None else ROOT
    override = os.environ.get('ROLEWEAVER_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if (root/'installation.json').is_file():
        local = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData/Local')
        return local/'RoleWeaver'/'ModuleStudio'
    return root/'data'
