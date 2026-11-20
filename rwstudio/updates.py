"""Explicit, checksum-verified native release updates; workspace data stays separate."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import urllib.error
import urllib.request
import uuid
import zipfile

from . import VERSION
from .paths import ROOT

REPO = 'RoleWeaverInfo/RWSoloSuite'
API = 'https://api.github.com/repos/'+REPO
RELEASES = 'https://github.com/'+REPO+'/releases'
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
MAX_PACKAGE = 2_000_000_000


def external_environment():
    env = os.environ.copy()
    if getattr(sys, 'frozen', False):
        original = env.pop('LD_LIBRARY_PATH_ORIG', None)
        if original is None:env.pop('LD_LIBRARY_PATH', None)
        else:env['LD_LIBRARY_PATH'] = original
        env.pop('DYLD_LIBRARY_PATH', None)
    return env


def github_cli():
    found = shutil.which('gh')
    if found:return found
    if sys.platform == 'darwin':
        # Finder does not inherit a Terminal's Homebrew PATH.
        return next((p for p in ('/opt/homebrew/bin/gh', '/usr/local/bin/gh') if Path(p).is_file()), None)
    return None


def version_key(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)[.-]?(\d+))?', value)
    if not match:return None
    major, minor, patch, phase, number = match.groups()
    return (int(major), int(minor), int(patch), {None:3, 'rc':2, 'beta':1, 'alpha':0}[phase], int(number or 0))


def package_suffix(system=None, machine=None):
    system = system or sys.platform
    arch = (machine or platform.machine()).lower()
    arch = {'amd64':'x64', 'x86_64':'x64', 'arm64':'arm64', 'aarch64':'arm64'}.get(arch)
    if system == 'win32' and arch == 'x64':return 'Setup-x64.exe'
    if system == 'darwin' and arch:return 'macOS-'+arch+'.zip'
    if system.startswith('linux') and arch:return 'Linux-'+arch+'.tar.gz'
    raise ValueError('No native update package is available for this operating system and architecture.')


def install_location():
    if sys.platform == 'win32' and (ROOT/'installation.json').is_file():return ROOT.resolve()
    if getattr(sys, 'frozen', False):
        exe = Path(sys.executable).resolve()
        return exe.parents[2] if sys.platform == 'darwin' else exe.parent
    return None


def release_list():
    request = urllib.request.Request(API+'/releases?per_page=100', headers={'Accept':'application/vnd.github+json', 'User-Agent':'RoleWeaver-Module-Studio'})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read(5_000_000)), False
    except urllib.error.HTTPError as error:
        if error.code not in (401, 403, 404, 429):raise ValueError('GitHub could not check updates (HTTP '+str(error.code)+'). Retry later.') from None
        # Private releases may use the user's existing CLI sign-in. Never read,
        # store, log or distribute a GitHub token in the application.
        gh = github_cli()
        if gh:
            result = subprocess.run([gh, 'api', 'repos/'+REPO+'/releases?per_page=100'], capture_output=True, timeout=30, creationflags=NO_WINDOW, env=external_environment())
            if result.returncode == 0:return json.loads(result.stdout), True
        if error.code in (403, 429):raise ValueError('GitHub temporarily limited or refused the update check. Retry later, or use Open official releases. An existing GitHub CLI sign-in may allow another check.') from None
        raise ValueError('The release repository requires GitHub access. Sign in with GitHub CLI (gh auth login) using an account with repository access, or download a release from GitHub. No shared access key is included.') from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Cannot reach GitHub. Check your internet connection and retry.') from None


def select_release(releases, current=VERSION, suffix=None):
    current_key = version_key(current)
    if current_key is None:raise ValueError('The installed version cannot be compared safely.')
    suffix = suffix or package_suffix()
    candidates = []
    for release in releases:
        key = version_key(release.get('tag_name', ''))
        # Stable installations stay on stable releases. RC installations can
        # receive newer candidates and the subsequent stable version.
        if release.get('draft') or not key or key <= current_key:continue
        if (release.get('prerelease') or key[3] < 3) and current_key[3] == 3:continue
        candidates.append((key, release))
    if not candidates:return None
    release = max(candidates, key=lambda row:row[0])[1]
    tag = release['tag_name'];name = 'Role-Weaver-Module-Studio-'+tag.removeprefix('v')+'-'+suffix
    asset = next((a for a in release.get('assets', []) if a.get('name') == name), None)
    if not asset:raise ValueError('The newest release has no package for this platform yet. Retry after its builds finish.')
    digest = asset.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):raise ValueError('This release has no verifiable SHA-256 asset digest. Use the release page to install it manually.')
    if type(asset.get('id')) is not int or type(asset.get('size')) is not int or not 0 < asset['size'] <= MAX_PACKAGE:
        raise ValueError('Invalid release package metadata.')
    return dict(version=tag.removeprefix('v'), tag=tag, name=name, asset_id=asset['id'], size=asset['size'], sha256=digest[7:], url=RELEASES+'/tag/'+tag)


def download(candidate, destination, authenticated=False):
    if authenticated:
        gh = github_cli()
        if not gh:raise ValueError('GitHub CLI is required to download this private release.')
        with destination.open('wb') as stream:
            result = subprocess.run([gh, 'api', 'repos/'+REPO+'/releases/assets/'+str(candidate['asset_id']), '-H', 'Accept: application/octet-stream'], stdout=stream, stderr=subprocess.PIPE, timeout=900, creationflags=NO_WINDOW, env=external_environment())
        if result.returncode:raise ValueError('GitHub could not download the private release. Check repository access and retry.')
    else:
        # URLs are constructed from the fixed repository and validated version;
        # no client-supplied URL, executable path or command is accepted.
        url = RELEASES+'/download/'+candidate['tag']+'/'+candidate['name']
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'RoleWeaver-Module-Studio'}), timeout=60) as response, destination.open('wb') as stream:
            total = 0
            while chunk := response.read(1024*1024):
                total += len(chunk)
                if total > candidate['size']:raise ValueError('Download exceeds the published package size.')
                stream.write(chunk)
    verify_download(candidate, destination)


def verify_download(candidate, destination):
    if destination.stat().st_size != candidate['size']:raise ValueError('Incomplete update download. Retry before installing.')
    with destination.open('rb') as stream:digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != candidate['sha256']:raise ValueError('The update checksum does not match GitHub. Nothing was installed.')


def safe_member(name):
    path = PurePosixPath(name)
    if not name or '\\' in name or path.is_absolute() or '..' in path.parts or ':' in name:
        raise ValueError('Unsafe path in update archive.')
    return path


def unpack(package, destination, system=None):
    system = system or sys.platform
    destination.mkdir()
    if system == 'darwin':
        # Write regular files first; create links last so archive entries never
        # write through a link. Only links to existing in-bundle targets pass.
        links = []
        with zipfile.ZipFile(package) as archive:
            for info in archive.infolist():
                name = safe_member(info.filename)
                if name.parts[0] == '__MACOSX':continue
                if name.parts[0] != 'Role Weaver Module Studio.app':raise ValueError('Unexpected Mac update layout.')
                target = destination.joinpath(*name.parts);mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    links.append((target, archive.read(info).decode('utf-8')));continue
                if info.is_dir():target.mkdir(parents=True, exist_ok=True);continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open('xb') as output:shutil.copyfileobj(source, output)
                target.chmod(mode & 0o755 or 0o644)
        bundle = destination/'Role Weaver Module Studio.app'
        for target, link in links:
            if Path(link).is_absolute() or not (target.parent/link).resolve().is_relative_to(bundle.resolve()):
                raise ValueError('Unsafe link in Mac update.')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(link)
        for target, _ in links:
            if not target.resolve().is_relative_to(bundle.resolve()) or not target.exists():raise ValueError('Invalid Mac update link.')
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(bundle)], check=True, capture_output=True, env=external_environment())
        exe = bundle/'Contents/MacOS/RoleWeaverModuleStudio'
    else:
        with tarfile.open(package, 'r:gz') as archive:
            for member in archive.getmembers():
                path = safe_member(member.name)
                if path.parts[0] != 'RoleWeaverModuleStudio':raise ValueError('Unexpected Linux update layout.')
            archive.extractall(destination, filter='data')
        bundle = destination/'RoleWeaverModuleStudio';exe = bundle/'RoleWeaverModuleStudio'
    if not exe.is_file():raise ValueError('The package has no Role Weaver service executable.')
    return bundle


def helper_script(install, package, staged, data, pid, work, system=None):
    """Detached helper waits for shutdown; never deletes projects or old installs."""
    system = system or sys.platform
    if system == 'win32':
        quote = lambda p:"'"+str(p).replace("'", "''")+"'"
        # Per-user Inno Setup updates this exact install directory. On failure
        # the log remains available and the original service is restarted.
        return '\n'.join([
            "$ErrorActionPreference = 'Stop'",
            '$deadline = (Get-Date).AddMinutes(2)',
            f'while (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ if ((Get-Date) -gt $deadline) {{ throw "Service did not stop; update cancelled" }}; Start-Sleep -Milliseconds 500 }}',
            '$setupArgs = @("/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", '+quote('/DIR="'+str(install)+'"')+', '+quote('/LOG="'+str(work/'installer.log')+'"')+')',
            f'$process = Start-Process -FilePath {quote(package)} -ArgumentList $setupArgs -Wait -PassThru -WindowStyle Hidden',
            f'$env:ROLEWEAVER_DATA_DIR = {quote(data)}',
            f'Start-Process -FilePath {quote(install/"Role Weaver Module Studio.exe")} -WorkingDirectory {quote(install)} -WindowStyle Hidden',
            'if ($process.ExitCode -ne 0) { throw "Installer returned $($process.ExitCode). See installer.log." }',
        ])+'\n'
    q = shlex.quote
    backup = install.with_name(install.name+'.before-update-'+work.name)
    replacement = install.with_name(install.name+'.update-'+work.name)
    executable = install/('Contents/MacOS/RoleWeaverModuleStudio' if system == 'darwin' else 'RoleWeaverModuleStudio')
    # Copy into the target filesystem before renaming. A failed swap restores
    # the previous bundle; no recursive removal and no shell-built user commands.
    return '\n'.join([
        '#!/bin/sh', 'set -eu',
        'n=0', f'while kill -0 {pid} 2>/dev/null; do n=$((n + 1)); [ "$n" -lt 120 ] || exit 1; sleep 1; done',
        f'test ! -e {q(str(backup))}', f'test ! -e {q(str(replacement))}',
        f'cp -pR {q(str(staged))} {q(str(replacement))}',
        f'mv {q(str(install))} {q(str(backup))}',
        f'if ! mv {q(str(replacement))} {q(str(install))}; then mv {q(str(backup))} {q(str(install))}; exit 1; fi',
        f'export ROLEWEAVER_DATA_DIR={q(str(data))}',
        'export PYINSTALLER_RESET_ENVIRONMENT=1',
        'unset LD_LIBRARY_PATH LD_LIBRARY_PATH_ORIG DYLD_LIBRARY_PATH',
        f'nohup {q(str(executable))} >{q(str(work/"restart.log"))} 2>&1 &',
    ])+'\n'


class Updater:
    def __init__(self, data):
        self.data = Path(data).resolve();self.lock = threading.RLock()
        self.result = dict(state='idle', current=VERSION, releases_url=RELEASES, installable=install_location() is not None)
        self.candidate = None;self.authenticated = False;self.package = None;self.staged = None;self.work = None

    def status(self):
        with self.lock:return dict(self.result)

    def start(self, operation):
        if operation not in ('check', 'download'):raise ValueError('Unknown update operation.')
        with self.lock:
            if self.result['state'] in ('checking', 'downloading', 'installing'):raise ValueError('An update operation is already running.')
            if operation == 'download' and (not self.candidate or not self.result['installable']):
                raise ValueError('Check for a newer release in an installed native version first. Source checkouts are never overwritten by the updater.')
            self.result.update(state='checking' if operation == 'check' else 'downloading', error='')
            threading.Thread(target=self._run, args=(operation,), daemon=True).start()
        return self.status()

    def _run(self, operation):
        try:
            if operation == 'check':
                releases, auth = release_list();candidate = select_release(releases)
                with self.lock:
                    self.candidate = candidate;self.authenticated = auth;self.package = None;self.staged = None
                    self.result.update(state='available' if candidate else 'current', release=candidate)
            else:
                self.work = self.data/'updates'/uuid.uuid4().hex
                self.work.mkdir(parents=True)
                self.package = self.work/self.candidate['name']
                download(self.candidate, self.package, self.authenticated)
                self.staged = unpack(self.package, self.work/'unpacked') if sys.platform != 'win32' else None
                with self.lock:self.result['state'] = 'ready'
        except Exception as error:
            with self.lock:self.result.update(state='error', error=str(error) if isinstance(error, ValueError) else 'Update operation failed. Check network access, free space and folder permissions, then retry.')

    def apply(self):
        with self.lock:
            if self.result['state'] != 'ready':raise ValueError('Download and verify a newer release before installing.')
            from .launcher import game_running
            if game_running():raise ValueError('Save and exit NWN before updating Role Weaver.')
            install = install_location()
            if not install or self.data.is_relative_to(install):raise ValueError('Automatic updates require an installed version with its workspace outside the application folder.')
            if not os.access(install.parent, os.W_OK):raise ValueError('This installation folder is not writable. Install the downloaded release manually.')
            verify_download(self.candidate, self.package)
            if sys.platform != 'win32':
                exe = self.staged/('Contents/MacOS/RoleWeaverModuleStudio' if sys.platform == 'darwin' else 'RoleWeaverModuleStudio')
                result = subprocess.run([str(exe), '--version'], capture_output=True, text=True, timeout=30, env=dict(external_environment(), PYINSTALLER_RESET_ENVIRONMENT='1'))
                if result.returncode or result.stdout.strip() != self.candidate['version']:
                    raise ValueError('The downloaded service cannot run on this computer or reports a different version. The current service is unchanged.')
            script = self.work/('apply.ps1' if sys.platform == 'win32' else 'apply.sh')
            script.write_text(helper_script(install, self.package, self.staged, self.data, os.getpid(), self.work), encoding='utf-8-sig' if sys.platform == 'win32' else 'utf-8')
            if sys.platform == 'win32':
                args = ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script)]
                options = dict(creationflags=NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                args = ['/bin/sh', str(script)];options = dict(start_new_session=True)
            with (self.work/'update.log').open('ab') as log:
                child = subprocess.Popen(args, cwd=self.work, env=external_environment(), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **options)
            self.result.update(state='installing', helper_pid=child.pid, log=str(self.work/'update.log'))
            return self.status()
