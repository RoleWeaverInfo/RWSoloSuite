"""Module archive filenames are not the 16-byte resource names inside them."""
import hashlib
import re

# Studio's portable filename policy, excluding the .mod extension. Keep paths
# manageable on Windows and use the same rule for exports and both launchers.
MAX_MODULE_NAME = 64
MODULE_NAME_PATTERN = r'[a-z][a-z0-9_]{0,63}'
MODULE_NAME_HELP = ('Use a module filename of 1–64 lowercase letters, digits or '
                    'underscores, starting with a letter, without .mod or a path.')


def valid_module_name(name):
    return isinstance(name, str) and re.fullmatch(MODULE_NAME_PATTERN, name) is not None


def validate_module_name(name):
    if not valid_module_name(name):
        raise ValueError(MODULE_NAME_HELP)
    return name


def module_tag(name):
    """Keep generated module tags within 32 characters, independently of files."""
    validate_module_name(name)
    if len(name) <= 32:
        return name
    return name[:23] + '_' + hashlib.sha256(name.encode('ascii')).hexdigest()[:8]
