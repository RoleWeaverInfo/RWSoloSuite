"""Remove reviewed void engine calls, preserving arguments' evaluation and branches.

This is not a decompiler. It accepts only fully decoded NCS and known scalar
signatures. Deferred actions are deliberately excluded until their saved PCs can
be relocated and tested. No offset from a browser or saved profile is trusted.
"""
import struct
from .script_analysis import analyse

VOID_CALLS = {'AddJournalQuestEntry', 'RemoveJournalQuestEntry', 'GiveGoldToCreature', 'GiveXPToCreature'}


def suppress(raw, actions, selections):
    report = analyse(raw, actions, include_instructions=True)
    if report['status'] != 'decoded': raise ValueError('Compiled mission script is not completely decoded')
    rows = report['bytecode']; calls = {c['offset']: c for c in report['calls']}
    if any(r['op'] == 'STORESTATE' for r in rows):
        raise ValueError('Deferred actions in this script require a dedicated conversion adapter')
    replacements = {}
    for offset, expected in selections.items():
        call = calls.get(offset)
        if not call or call['name'] != expected or expected not in VOID_CALLS:
            raise ValueError('Native mission call no longer matches the reviewed evidence')
        row = next(r for r in rows if r['offset'] == offset)
        action_id, argc = row['operand']; definition = actions.get(action_id, {})
        types = definition.get('types', [])[:argc]
        if definition.get('return') != 'void' or len(types) != argc or not types or any(t not in ('int', 'float', 'string', 'object') for t in types):
            raise ValueError('Unsupported native mission call signature')
        # ACTION pops scalar arguments without a return value. MOVSP does exactly
        # that, including releasing strings; expressions producing them still run.
        replacements[offset] = b'\x1b\x00' + struct.pack('>i', -4 * argc)
    positions = {}; cursor = 13
    for row in rows:
        positions[row['offset']] = cursor
        cursor += len(replacements.get(row['offset'], raw[row['offset']:row['end']]))
    body = bytearray()
    for row in rows:
        chunk = replacements.get(row['offset'], raw[row['offset']:row['end']])
        if 'target' in row:
            if row['target'] not in positions: raise ValueError('Unresolved compiled branch target')
            chunk = chunk[:2] + struct.pack('>i', positions[row['target']] - positions[row['offset']])
        body.extend(chunk)
    result = b'NCS V1.0\x42' + struct.pack('>I', 13 + len(body)) + body
    checked = analyse(result, actions)
    if checked['status'] != 'decoded': raise ValueError('Patched mission bytecode failed validation')
    remaining = [c['name'] for c in report['calls'] if c['offset'] not in selections]
    if remaining != [c['name'] for c in checked['calls']]: raise ValueError('An unrelated engine call changed')
    return result
