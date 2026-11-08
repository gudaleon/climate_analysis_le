"""Addendum A: map claims to inventory sections; list Abstract / Discussion / Conclusion claims whose recomputed checks change T->S."""
import re, sys, pandas as pd
PK = '/home/hatch/workspace/jeremy_wu_redteam/packs/'
def sections(f, pre):
    sec = None; out = {}; txt = {}
    for line in open(PK + f):
        if line.startswith('#'): sec = line.strip('# \n')
        m = re.match(r'^- \*\*(' + pre + r'\d+)\.\*\* (.*)$', line.strip())
        if m: out[m.group(1)] = sec; txt[m.group(1)] = m.group(2)
    return out, txt
S6, T6 = sections('CLAIMS_INVENTORY_613.md', 'C'); S7, T7 = sections('CLAIMS_INVENTORY_v7.md', 'V7-C')
def adc(sec, tgt):
    if sec is None: return None
    if sec.startswith('Abstract'): return 'Abstract'
    if tgt == '613':
        if 'Discussion' in sec or sec.startswith('Section 4'): return 'Discussion'
        if 'Conclusion' in sec: return 'Conclusion'
    else:
        if re.match(r'^4(\.|\b)', sec) or sec.startswith('4.'): return 'Discussion'
        if re.match(r'^5(\.|\b)', sec): return 'Conclusion'
    return None
if __name__ == '__main__':
    print(sorted(set(S7.values()))[:80])
    d = pd.read_csv('out_addA/claim_check_changes.csv')
    d['sec'] = [ (S6 if t == '613' else S7).get(c) for t, c in zip(d.target, d.claim)]
    d['adc'] = [adc(s, t) for s, t in zip(d.sec, d.target)]
    d['text'] = [(T6 if t == '613' else T7).get(c, '') for t, c in zip(d.target, d.claim)]
    d.to_csv('out_addA/claim_check_changes_sec.csv', index=False)
    a = d[d.adc.notna()]
    for (t, c), g in a.groupby(['target', 'claim'], sort=False):
        print(f'\n## {c} [{g.adc.iloc[0]} | {g.sec.iloc[0]}] {g.text.iloc[0][:600]}')
        for r in g.itertuples(): print(f'   {r.check}: printed {r.printed} | T {r.T} | S {r.S} | T-match {r.printed_matches_T} S-match {r.printed_matches_S}')
