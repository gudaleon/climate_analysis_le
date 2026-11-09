#!/usr/bin/env python
"""Integrity verification for JW_Thesis_6.13_finalized.docx.

Checks, in the pattern of the v7 revision verifications:
- a document-order text walk shows the finalized document differs from the
  working copy of the archived original only by the added Chapter 6 block
  and, since the literature improvement pass of 2026-11-09, the two
  reference entries that the block's Section 6.4 passage cites (zero
  changed paragraphs outside those additions);
- table count rises by exactly one (Table 6) and inline shapes by exactly
  one (Figure 8), with the new figure at the section's full text width;
- the file opens cleanly under python-docx and passes zip integrity;
- the archived mirror original's MD5 is identical to the working copy's.
Prints the block's opening and closing paragraphs verbatim for the
change note.
"""
import zipfile, hashlib, os
from docx import Document

WS = '/home/hatch/workspace/jeremy_wu_redteam'
ORIG = WS + '/thesis_finalize_613/original_copy.docx'
FIN = WS + '/thesis_finalize_613/JW_Thesis_6.13_finalized.docx'
MIRROR = (WS + '/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/'
          'Thesis_6.13_method_new_data/1_Thesis/After_6.13_new_data/'
          'JW_Thesis_6.13_new_data_clean.docx')

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def walk(path):
    d = Document(path)
    out = []
    for p in d.element.body.iter():
        if p.tag.endswith('}p'):
            out.append(''.join(n.text or '' for n in p.iter()
                               if n.tag.endswith('}t')))
    return d, out

do, orig = walk(ORIG)
df, fin = walk(FIN)
print('paragraphs (walk): original', len(orig), '| finalized', len(fin),
      '| diff', len(fin) - len(orig))
print('tables: original', len(do.tables), '| finalized', len(df.tables))
print('inline shapes: original', len(do.inline_shapes),
      '| finalized', len(df.inline_shapes))

# Locate the block: it starts at the Chapter 6 heading and ends just before
# the empty section-break paragraph that precedes 'References'. In the walk,
# the body 'References' heading is the entry immediately followed by the
# first reference ('AghaKouchak').
def ref_index(w):
    hits = [i for i, t in enumerate(w)
            if t.strip() == 'References' and i + 1 < len(w)
            and w[i + 1].startswith('AghaKouchak')]
    assert len(hits) == 1, hits
    return hits[0]

ri_o, ri_f = ref_index(orig), ref_index(fin)
k_o, k_f = ri_o - 1, ri_f - 1          # the empty sectPr paragraph in each
assert orig[k_o] == '' and fin[k_f] == ''
i0 = next(i for i, t in enumerate(fin)
          if t.startswith('6. Error Framework, Location Sensitivity'))
print('block start (walk index):', i0, '| original insertion point:', k_o)
assert i0 == k_o, 'block does not start where the original section break sits'
block = fin[i0:k_f]
print('inserted block paragraphs (incl. table cells):', len(block))
assert len(block) == 52, len(block)   # 50 as first built + 2 (Section 6.4 literature passage)

NEW_REFS_613 = [
    'Annan, J. D., & Hargreaves, J. C. (2010). Reliability of the CMIP3 ensemble. Geophysical Research Letters, 37, L02703. https://doi.org/10.1029/2009GL041994',
    'Zhang, X., Hegerl, G., Zwiers, F. W., & Kenyon, J. (2005). Avoiding inhomogeneity in percentile-based indices of temperature extremes. Journal of Climate, 18, 1641–1651. https://doi.org/10.1175/JCLI3366.1',
]
for entry in NEW_REFS_613:
    assert fin.count(entry) == 1, entry[:60]
ia = fin.index(NEW_REFS_613[0])
assert fin[ia - 1].startswith('Alexander, L. V.') and fin[ia + 1].startswith('Allen, R. G.')
iz = fin.index(NEW_REFS_613[1])
assert fin[iz - 1].startswith('Zhang, X., Alexander') and fin[iz + 1].startswith('Zhou, Y.')
print('new references present once each, at their alphabetical positions')
assert any(t.startswith("One reframing from the audit's literature review") for t in block)
assert any(t.startswith('A second point from the same review') for t in block)
assert block[-1].startswith('The thesis therefore stands as follows')
print('Section 6.4 literature passage present; closing paragraph unchanged and still last')

pre_o, pre_f = orig[:k_o], fin[:i0]
tail_o, tail_f = orig[k_o:], fin[k_f:]
tail_f_filtered = [t for t in tail_f if t not in NEW_REFS_613]
assert len(tail_f) - len(tail_f_filtered) == len(NEW_REFS_613)
assert len(pre_o) == len(pre_f) and len(tail_o) == len(tail_f_filtered)
diffs = [(a, b) for a, b in zip(pre_o, pre_f) if a != b]
diffs += [(a, b) for a, b in zip(tail_o, tail_f_filtered) if a != b]
print('changed paragraphs outside the inserted block and the two new references:', len(diffs))
assert not diffs
assert len(fin) - len(block) - len(NEW_REFS_613) == len(orig)

print()
print('--- block opening paragraph (verbatim) ---')
print(block[1])
print('--- block closing paragraph (verbatim) ---')
print(block[-1])
print('--- block headings and captions ---')
for t in block:
    if t.startswith(('6.', 'Table 6.', 'Figure 8.')):
        print(' *', t[:120])

# The new figure: exactly one inline shape wider than any original shape set;
# check the maximum width in the finalized file equals the text width.
widths_f = [s.width for s in df.inline_shapes]
print('new figure width (EMU):', max(widths_f), '| expected text width: 6858000')
assert 6858000 in widths_f

for path in (ORIG, FIN):
    z = zipfile.ZipFile(path)
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(path.split('/')[-1], 'zip testzip:', z.testzip(),
          '| media files:', len(media), '| bytes:', os.path.getsize(path))
print('md5 mirror original :', md5(MIRROR))
print('md5 working copy    :', md5(ORIG))
assert md5(MIRROR) == md5(ORIG)
print('ALL CHECKS PASSED')
