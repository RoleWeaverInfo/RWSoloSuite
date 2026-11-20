"""Verified HTTPS using OS roots plus bundled roots in frozen applications."""
import ssl
import sys

def context():
    result=ssl.create_default_context()
    if getattr(sys,'frozen',False):
        # Python's compiled-in CA path points at the build runner on native Mac
        # bundles. Certifi supplies portable roots without disabling verification.
        import certifi
        result.load_verify_locations(cafile=certifi.where())
    return result
