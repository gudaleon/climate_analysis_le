#!/usr/bin/env python
"""Integrity verification: original vs revised v7 thesis."""
import json, zipfile
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

WS = '/home/hatch/workspace/jeremy_wu_redteam'
ORIG = WS + '/thesis_revision/original_copy.docx'
REV = WS + '/thesis_revision/JW_Thesis_revised_v7_with_insert.docx'
MIRROR = (WS + '/drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/'
          'Thesis_v7_defence_framework_new_data/1_Thesis/After_v7_defence/'
          'JW_Thesis_revised_v7_clean.docx')

def walk(doc):
    """All paragraph texts in document order, recursing into tables."""
    out = []
    def rec(parent):
        for child in parent.element.body.iterchildren() if hasattr(parent, 'element') and parent.__class__.__name__ == 'Document' else []:
            pass
    # simpler: iterate top-level body children
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit('}', 1)[-1]
        if tag == 'p':
            out.append(('P', Paragraph(child, doc).text))
        elif tag == 'tbl':
            t = Table(child, doc)
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        out.append(('C', p.text))
    return out

import hashlib, os
def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

do = Document(ORIG)
dr = Document(REV)
so, sr = walk(do), walk(dr)
print('original paragraphs (incl. table cells):', len(so))
print('revised  paragraphs (incl. table cells):', len(sr))

# Locate the inserted block in the revised sequence: from the 3.6 heading
# to just before the '4. Discussion' heading.
i0 = next(i for i, (k, t) in enumerate(sr) if t.startswith('3.6 Robustness'))
i1 = next(i for i, (k, t) in enumerate(sr) if t == '4. Discussion')
block = sr[i0:i1]
print('inserted block paragraphs:', len(block))
sr_stripped = sr[:i0] + sr[i1:]

assert len(sr_stripped) == len(so), (len(sr_stripped), len(so))
record = json.load(open(WS + '/thesis_revision/qualifications.json'))
diffs = []
for idx, ((ko, to), (kr, tr)) in enumerate(zip(so, sr_stripped)):
    assert ko == kr
    if to != tr:
        diffs.append((idx, to, tr))
print('changed paragraphs outside inserted block:', len(diffs))
for idx, to, tr in diffs:
    print('--- changed para (orig index', idx, ')')
    print('ORIG tail:', repr(to[-160:]))
    print('REV  tail:', repr(tr[-260:]))

# Confirm each change is exactly one of the recorded qualifications
tails = [d[2][-len(d[1]):] if False else None for d in diffs]
for key, (before, after) in record.items():
    ok = any(before in to and after in tr for _, to, tr in diffs)
    print(key, 'qualification verified in diff:', ok)

# Tables / figures / media
print('tables: orig', len(do.tables), '-> revised', len(dr.tables))
print('inline shapes: orig', len(do.inline_shapes), '-> revised', len(dr.inline_shapes))
for label, path in (('original', ORIG), ('revised', REV)):
    z = zipfile.ZipFile(path)
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(label, 'media files:', len(media), '| zip test:', z.testzip())
    print(label, 'size bytes:', os.path.getsize(path))
print('mirror md5 == working-copy md5:', md5(MIRROR) == md5(ORIG))
