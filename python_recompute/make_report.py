import json, re
h = open('report_head.md').read()
i4 = h.index('## 4. Pass 2 audit log'); i2 = h.index('## 2. Verdict table')
part1 = h[:i4]; middle = h[i4:i2]; t1head = h[i2:]
v = json.load(open('out/verdicts_613.json')); w = json.load(open('out/verdicts_v7.json'))
inv6 = {}; inv7 = {}
for line in open('/home/hatch/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_613.md'):
    m = re.match(r'^- \*\*(C\d+)\.\*\* (.*)$', line.strip())
    if m: inv6[m.group(1)] = m.group(2)
for line in open('/home/hatch/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_v7.md'):
    m = re.match(r'^- \*\*(V7-C\d+)\.\*\* (.*)$', line.strip())
    if m: inv7[m.group(1)] = m.group(2)
esc = lambda s: str(s).replace('|', '\\|').replace('\n', ' ')
def table(res, inv):
    out = ['| Claim | Printed (claim summary / printed values) | Mine (independent recompute, V4 layer) | Verdict | Pass-1 fork / evidence |', '|---|---|---|---|---|']
    keys = sorted(inv, key=lambda k: int(k.split('C')[-1]))
    for k in keys:
        r = res.get(k)
        if r is None:
            out.append(f'| {k} | {esc(inv[k][:200])} | not evaluated | CANNOT VERIFY | no rule |'); continue
        summ = inv[k][:160] + ('…' if len(inv[k]) > 160 else '')
        if r['kind'] == 'num':
            printed = f"{summ} — printed values: {r['printed']}"
            ev = f"Pass-1 (own homogenisation): {r.get('h1')}" + ('; literature part not checkable' if r.get('lit') else '')
        elif r['kind'] == 'table':
            printed = summ; ev = r.get('evidence') or 'all cells reproduced'
        else:
            printed = f"{summ} — printed: {r['printed']}"; ev = r.get('evidence', '')
        out.append(f"| {k} | {esc(printed)} | {esc(r['mine'])} | **{r['verdict']}** | {esc(ev)} |")
    return '\n'.join(out)
rep = part1 + t1head + '\n' + table(v, inv6) + '\n\n---\n\n## 3. Verdict table — Target 2 (v7 version)\n\nSame columns and conventions as Section 2. † = reproduced by my statistics on the authors\' annual index tables; my own index recompute differs only through the data-layer defects S3–S5 (see the discrepancy log).\n\n' + table(w, inv7) + '\n\n---\n\n' + middle
open('REPORT_WuThesis_ClaudeCodeVM_2026-11-07.md', 'w').write(rep)
print(len(rep), rep.count('\n'))
from collections import Counter
print(Counter(re.findall(r'\| \*\*(CONFIRMED|DISPUTED|CANNOT VERIFY)\*\* \|', rep)))
