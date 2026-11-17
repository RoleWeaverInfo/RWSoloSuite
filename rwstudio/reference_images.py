"""Bounded portable floor-plan images, validated before they reach a provider."""
import base64
import binascii
import re

def image_data(url):
    match=re.fullmatch(r'data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)',url if isinstance(url,str) else '')
    if not match or len(url)>3_000_000:raise ValueError('Use a PNG, JPEG or WebP floor plan of at most 2 MB.')
    try:raw=base64.b64decode(match[2],validate=True)
    except (ValueError,binascii.Error):raise ValueError('Invalid image encoding') from None
    mime=match[1]
    good={'image/png':raw.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':raw.startswith(b'\xff\xd8\xff'),'image/webp':raw.startswith(b'RIFF') and raw[8:12]==b'WEBP'}
    if not good[mime] or len(raw)>2_000_000:raise ValueError('Image contents do not match a supported file type or size.')
    return mime,match[2]

def validate_references(project):
    total=0
    for area in project['areas']:
        refs=area.get('references',[])
        if len(refs)>3:raise ValueError('Use at most three reference images per area.')
        for ref in refs:
            image_data(ref['data_url']);total+=len(ref['data_url'])
            if len(ref['name'])>120 or len(ref['notes'])>3000:raise ValueError('Reference name or notes are too long.')
    if total>12_000_000:raise ValueError('Total reference images exceed the 12 MB project limit.')
