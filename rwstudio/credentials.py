"""OS-protected local credentials; never included in project exports."""
import base64
import ctypes
from ctypes import wintypes
import json
import os
import sys
import hashlib
from pathlib import Path
from .storage import write_json

ENV={'openai':'OPENAI_API_KEY','gemini':'GEMINI_API_KEY'}


def system_keyring():
    # Only OS secret stores; never select a third-party plaintext fallback.
    try:
        if sys.platform=='darwin':
            from keyring.backends.macOS import Keyring
        elif sys.platform.startswith('linux'):
            from keyring.backends.SecretService import Keyring
        else:raise ValueError('Unsupported credential platform')
        return Keyring()
    except Exception:
        raise ValueError('Secure key storage is unavailable. Unlock your macOS Keychain or Linux Secret Service keyring, or use an environment key.') from None

def protect(raw, decrypt=False):
    if os.name!='nt':raise ValueError('Saving keys requires Windows credential protection; use environment variables on this system.')
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    fn.restype=wintypes.BOOL;kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):raise ValueError('Windows could not access the saved credential for this user.')
    try:return ctypes.string_at(target.data,target.size)
    finally:kernel.LocalFree(target.data)

class Credentials:
    def __init__(self,root):self.path=Path(root)/'credentials.json'
    def records(self):return json.loads(self.path.read_text(encoding='utf8')) if self.path.exists() else {}
    def keyring_account(self,provider):return hashlib.sha256(str(self.path.resolve()).encode()).hexdigest()[:24]+':'+provider
    def keyring_call(self,method,provider,*args):
        try:return getattr(system_keyring(),method)('RoleWeaver.ModuleStudio',self.keyring_account(provider),*args)
        except Exception:
            raise ValueError('Secure key storage could not be accessed. Unlock your macOS Keychain or Linux Secret Service keyring, or use an environment key.') from None
    def get(self,provider):
        if provider not in ENV:raise ValueError('Unknown AI provider')
        value=self.records().get(provider)
        if value:
            if isinstance(value,dict) and value.get('storage')=='keyring':
                key=self.keyring_call('get_password',provider)
                if not key:raise ValueError('The saved key is missing from this computer’s keyring. Save it again.')
                return key
            return protect(base64.b64decode(value),True).decode('utf8')
        return os.environ.get(ENV[provider],'')
    def status(self):
        saved=self.records();out={}
        for p in ENV:
            try:out[p]={'saved':p in saved,'available':bool(self.get(p))}
            except ValueError:out[p]={'saved':p in saved,'available':False,'error':'Unlock this computer’s credential store, or re-enter this key for the current user account.'}
        return out
    def update(self,provider,key=None,remove=False):
        if provider not in ENV:raise ValueError('Unknown AI provider')
        records=self.records()
        if remove:
            if isinstance(records.get(provider),dict) and records[provider].get('storage')=='keyring':
                if self.keyring_call('get_password',provider):self.keyring_call('delete_password',provider)
            records.pop(provider,None)
        else:
            if not isinstance(key,str) or not 8<=len(key.strip())<=4096 or any(c.isspace() for c in key.strip()):raise ValueError('Enter a valid API key without whitespace.')
            if sys.platform=='win32':records[provider]=base64.b64encode(protect(key.strip().encode())).decode('ascii')
            else:
                self.keyring_call('set_password',provider,key.strip())
                records[provider]={'storage':'keyring'}
        write_json(self.path,records)
        return self.status()
