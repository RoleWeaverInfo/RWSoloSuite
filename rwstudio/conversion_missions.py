"""Editable journal text and a private, evidence-linked map of native missions.

Review links are author annotations, never replacements for compiled quest logic.
Only explicitly edited journal names/text may change an imported game resource.
"""
import copy
import re
import struct

from .nwn.gff import read, write
from .nwn.analysis_formats import Archive, gff


def stage_key(quest, stage):
    return quest['id'] + ':' + stage['id']


def workspace(report):
    quests = []
    for i, q in enumerate(report['quests']):
        quests.append(dict(id=f'nq_{i}', tag=q['tag'], source=q['source'], name=q['name'], notes='',
                           stages=[dict(id=f's_{j}', native_id=e['id'], text=e['text'], end=e['end'],
                                        label=f"Entry {e['id']}", notes='') for j, e in enumerate(q['entries'])]))
    return dict(version=1, storyline='', quests=quests, links=[])


def _text(value, name, limit, nonempty=False):
    if (not isinstance(value, str) or len(value) > limit or '\x00' in value
            or (nonempty and not value.strip())):
        raise ValueError('Invalid mission editor ' + name)


def validate(value, report=None):
    if not isinstance(value, dict) or set(value) != {'version', 'storyline', 'quests', 'links'} or type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Unsupported native mission editor data')
    _text(value['storyline'], 'storyline', 20000)
    if not isinstance(value['quests'], list) or len(value['quests']) > 500:
        raise ValueError('Mission editor supports up to 500 journal quests')
    ids = set(); nodes = set(); count = 0
    for q in value['quests']:
        if not isinstance(q, dict) or set(q) != {'id', 'tag', 'source', 'name', 'notes', 'stages'}:
            raise ValueError('Invalid native mission fields')
        _text(q['id'], 'quest identity', 16, True)
        if not re.fullmatch(r'nq_[0-9]+', q['id']) or q['id'] in ids:
            raise ValueError('Invalid or duplicate native mission identity')
        ids.add(q['id']); nodes.add(q['id'])
        for field, limit in [('name', 500), ('tag', 128), ('source', 300), ('notes', 6000)]:
            _text(q[field], field, limit)
        if not isinstance(q['stages'], list) or len(q['stages']) > 2000:
            raise ValueError('Invalid native journal stages')
        stage_ids = set()
        for s in q['stages']:
            count += 1
            if not isinstance(s, dict) or set(s) != {'id', 'native_id', 'text', 'end', 'label', 'notes'}:
                raise ValueError('Invalid native stage fields')
            _text(s['id'], 'stage identity', 16, True)
            if not re.fullmatch(r's_[0-9]+', s['id']) or s['id'] in stage_ids:
                raise ValueError('Invalid or duplicate native stage identity')
            stage_ids.add(s['id']); nodes.add(stage_key(q, s))
            if s['native_id'] is not None and (type(s['native_id']) is not int or not 0 <= s['native_id'] <= 0xffffffff):
                raise ValueError('Invalid native journal entry number')
            if type(s['end']) is not bool:
                raise ValueError('Invalid native completion flag')
            for field, limit in [('text', 40000), ('label', 120), ('notes', 6000)]:
                _text(s[field], field, limit)
        if count > 10000:
            raise ValueError('Mission editor supports up to 10,000 journal stages')
    if not isinstance(value['links'], list) or len(value['links']) > 2000:
        raise ValueError('Mission editor supports up to 2,000 review links')
    pairs = set()
    for link in value['links']:
        if not isinstance(link, dict) or set(link) != {'from', 'to', 'label'}:
            raise ValueError('Invalid mission review link')
        for field in ('from', 'to'):
            _text(link[field], 'link endpoint', 40, True)
        _text(link['label'], 'link label', 200)
        pair = link['from'], link['to']
        if any(n not in nodes for n in pair) or pair[0] == pair[1] or pair in pairs:
            raise ValueError('Review links need two different existing nodes and cannot be duplicated')
        if (':' in pair[0]) != (':' in pair[1]):
            raise ValueError('Connect missions to missions, or stages to stages')
        if ':' in pair[0] and pair[0].split(':')[0] != pair[1].split(':')[0]:
            raise ValueError('Connect stages within one mission; use the overview for cross-mission notes')
        pairs.add(pair)
    if report is not None:
        base = workspace(report)
        identity = lambda w: [(q['id'], q['tag'], q['source'], [(s['id'], s['native_id'], s['end']) for s in q['stages']]) for q in w['quests']]
        if identity(value) != identity(base):
            raise ValueError('Native quest identities, entry numbers and completion flags must stay unchanged. Edit their text or review notes instead.')
    return copy.deepcopy(value)


def review(value, report):
    validate(value, report)
    base = workspace(report); changes = []; warnings = []
    for q, old in zip(value['quests'], base['quests']):
        if not q['name'].strip(): warnings.append(f"{q['tag']}: the journal name is empty.")
        if q['name'] != old['name']: changes.append(dict(quest=q['id'], stage='', field='name'))
        for s, original in zip(q['stages'], old['stages']):
            if s['text'] != original['text']: changes.append(dict(quest=q['id'], stage=s['id'], field='text'))
            if not s['text'].strip(): warnings.append(f"{q['name']} / Entry {s['native_id']}: journal text is empty.")
        if len(q['stages']) > 1 and not any(l['from'].startswith(q['id']+':') for l in value['links']):
            warnings.append(q['name']+': no reviewed stage links yet. Entry numbers do not establish progression.')
    return dict(errors=[], warnings=warnings, journal_changes=changes,
                note='Journal names/text are applied to the new copy. Storyline, labels, notes and arrows are private review annotations. Native scripts, rewards, entry numbers and completion flags stay unchanged.')


def evidence(report, path=None):
    """Collect direct journal writes separately from weak string associations."""
    result = {q['id']: {'sources': [], 'stages': {s['id']: [] for s in q['stages']}} for q in workspace(report)['quests']}
    base = workspace(report)
    for q, source in zip(base['quests'], report['quests']):
        target = result[q['id']]
        for e in source.get('script_evidence', []):
            row = dict(kind='Compiled script', source=e['script']+'.ncs', script=e['script'],
                       text=e['finding'], confidence='journal call' if 'journal_entry' in e else 'string association')
            if 'offset' in e: row['source'] += ' @ 0x'+format(e['offset'], 'x')
            target['sources'].append(row)
            for s in q['stages']:
                if type(e.get('journal_entry')) is int and e['journal_entry'] == s['native_id']:
                    target['stages'][s['id']].append(row)
    archive = Archive(path) if path else None
    for dlg in report['dialogues']:
        lines = dlg['lines']
        # Older saved analyses lack Quest/QuestEntry fields. Read only those fields
        # from the immutable local snapshot instead of forcing a costly re-import.
        native = gff(archive.get(dlg['id'], 2029)) if archive and (dlg['id'], 2029) in archive.index else {}
        speakers = sorted({c['name'] for c in report['characters'] if c.get('conversation') == dlg['id']})
        for line in lines:
            collection, index = line['id'].split(':'); rows = native.get(collection, [])
            original = rows[int(index)] if int(index) < len(rows) else {}
            tag = line.get('quest', original.get('Quest', ''))
            entry = line.get('quest_entry', original.get('QuestEntry'))
            if not tag: continue
            row = dict(kind='Native dialogue', source=line['source'], script=line.get('action', ''),
                       confidence='journal field', text=(' / '.join(speakers) or dlg['id'])+': '+line['text'][:1000])
            for q in base['quests']:
                if q['tag'] != tag: continue
                result[q['id']]['sources'].append(row)
                for s in q['stages']:
                    if type(entry) is int and entry == s['native_id']: result[q['id']]['stages'][s['id']].append(row)
    return result


def _localized(original, value):
    """Replace English text while retaining other embedded language variants."""
    _, count = struct.unpack_from('<II', original); pos = 8; parts = {}
    for _ in range(count):
        language, length = struct.unpack_from('<II', original, pos); pos += 8
        parts[language] = original[pos:pos+length]; pos += length
    parts[0] = value.encode('utf-8')
    if 1 in parts: parts[1] = value.encode('utf-8')  # Existing English feminine variant.
    return struct.pack('<II', 0xffffffff, len(parts)) + b''.join(struct.pack('<II', lang, len(data))+data for lang, data in parts.items())


def patch_journals(entries, report, value, skip_tags=()):
    """Apply the text-only allowlist, then reconstruct the original GFF exactly."""
    if value is None: return {}
    validate(value, report); base = workspace(report); documents = {}; changes = {}
    for q, old in zip(value['quests'], base['quests']):
        if q['tag'] in skip_tags:continue
        edits = [('name', None)] if q['name'] != old['name'] else []
        edits += [('text', i) for i, (s, original) in enumerate(zip(q['stages'], old['stages'])) if s['text'] != original['text']]
        if not edits: continue
        match = re.fullmatch(r'([a-z0-9_]{1,16})\.jrl/Categories\[([0-9]+)\]', old['source'], re.I)
        if not match: raise ValueError('This journal source cannot be edited safely: '+old['source'])
        key = match[1].lower(), 2056
        if key not in entries: raise ValueError('Original journal resource is missing')
        if key not in documents:
            kind, original = read(entries[key]); documents[key] = kind, original, copy.deepcopy(original), []
        kind, original, changed, restore = documents[key]
        index = int(match[2]); category = changed[1]['Categories'][1][index]
        for field, stage in edits:
            dest = category if stage is None else category[1]['EntryList'][1][stage]
            native_field = 'Name' if stage is None else 'Text'
            if native_field not in dest[1] or dest[1][native_field][0] != 12:
                raise ValueError('Unsupported journal text field: '+old['source'])
            restore.append((index, stage, native_field, dest[1][native_field]))
            text = q['name'] if stage is None else q['stages'][stage]['text']
            dest[1][native_field] = (12, _localized(dest[1][native_field][1], text))
            changes.setdefault(key[0], []).append(dict(quest_tag=q['tag'], entry=None if stage is None else q['stages'][stage]['native_id'], field=native_field))
    for key, (kind, original, changed, restore) in documents.items():
        restored = copy.deepcopy(changed)
        for index, stage, field, old in restore:
            dest = restored[1]['Categories'][1][index]
            if stage is not None: dest = dest[1]['EntryList'][1][stage]
            dest[1][field] = old
        if restored != original: raise ValueError('Journal preservation check failed')
        entries[key] = write(kind, changed)
    return changes
