"""Addendum A: render claim-by-claim change lists from out_addB/claim_check_changes_sec.csv."""
import pandas as pd, numpy as np, re, pickle
d = pd.read_csv('out_addB/claim_check_changes_sec.csv')
def v(x):
    try:
        x = float(x)
        return 'NA' if np.isnan(x) else (str(int(round(x))) if abs(x - round(x)) < 1e-9 else f'{x:.3f}'.rstrip('0').rstrip('.'))
    except Exception:
        return str(x)
def status(g):
    if (g.printed_matches_T & ~g.printed_matches_P).any(): return 'changes at printed precision'
    if (~g.printed_matches_T & ~g.printed_matches_P).all(): return 'already differs from print on T; value moves'
    return 'moves within printed rounding'
def block(sub, maxchecks=6):
    L = []
    for (t, c), g in sub.groupby(['target', 'claim'], sort=False):
        ch = '; '.join(f"{r.check}: printed {v(r.printed)}, T {v(r.T)}, P {v(r.P)}" for r in g.head(maxchecks).itertuples())
        if len(g) > maxchecks: ch += f'; … (+{len(g) - maxchecks} more checks)'
        L.append(f"- **{c}** ({g.sec.iloc[0]}; {status(g)}). {ch}.")
    return '\n'.join(L)
d['k'] = d.claim.str.extract(r'(\d+)').astype(int)
d = d.sort_values(['target', 'k'])
adc = d[d.adc.notna()]
tab = d.check.str.endswith(' p') | d.check.str.endswith(' arrow')
app = d.sec.fillna('').str.contains('Appendix|Table A|Table B|Table C')
body = d[d.adc.isna() & ~tab & ~app]
apx = d[d.adc.isna() & (tab | app)]
summ = apx.groupby(['target', 'sec']).agg(claims=('claim', 'nunique'), checks=('check', 'size'),
                                          flips=('printed_matches_P', lambda s: int((~s & apx.loc[s.index, 'printed_matches_T']).sum()))).reset_index()
pickle.dump(dict(ADC=block(adc, 8), BODY=block(body, 5), APX=summ, n_claims=d.groupby(['target', 'claim']).ngroups,
                 n_checks=len(d), n_flip=int((d.printed_matches_T & ~d.printed_matches_P).sum()),
                 per_t=d.groupby('target').claim.nunique().to_dict(),
                 per_t_flip=d[d.printed_matches_T & ~d.printed_matches_P].groupby('target').claim.nunique().to_dict()), open('out_addB/claim_parts.pkl', 'wb'))
print(block(adc, 8)[:3000]); print(summ.to_string()); print(d.groupby('target').claim.nunique())
print(d[d.printed_matches_T & ~d.printed_matches_P].groupby('target').claim.nunique())
