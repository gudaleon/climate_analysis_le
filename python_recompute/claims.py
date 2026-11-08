"""Load the two claims inventories into {id: text}; parse structured v7 table claims."""
import re

FULL = {'ACCESS-ESM1-5': 'ACCESS', 'BCC-CSM2-MR': 'BCC', 'CanESM5': 'CanESM', 'CNRM-ESM2-1': 'CNRM', 'EC-Earth3-Veg': 'EC',
        'GFDL-ESM4': 'GFDL', 'INM-CM5-0': 'INM', 'MIROC-ES2L': 'MIROC', 'MRI-ESM2-0': 'MRI', 'NorESM2-LM': 'NorESM'}


def load(path, prefix):
    out = {}
    for line in open(path):
        m = re.match(r'^- \*\*(' + prefix + r'\d+)\.\*\* (.*)$', line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def nums(s):
    return [float(x) for x in re.findall(r'(?<![A-Za-z0-9])[-−]?\d+(?:\.\d+)?', s.replace('−', '-'))]


def parse_v7_pvals(txt):
    m = re.search(r'for (London|Fergus|Harrow) station index (\S+) the Wilcoxon.*?Historical vs Historical panel.*?NorESM2-LM, as (.*?), and in the Present vs Present panel, in the same GCM order, as (.*?)\. \[', txt)
    if not m:
        return None
    f = lambda s: [None if x.strip() == 'nan' else float(x) for x in s.replace(' and ', ', ').split(',') if x.strip()]
    return m.group(1), m.group(2), f(m.group(3)), f(m.group(4))


def parse_v7_counts(txt):
    m = re.search(r'for (London|Fergus|Harrow) station the (temperature|precipitation)-related index pass counts.*?NorESM2-LM, as (.*?), and in the Present vs Present panel, in the same GCM order, as (.*?)\. \[', txt)
    if not m:
        return None
    f = lambda s: [int(x) for x in re.findall(r'\d+', s)]
    return m.group(1), m.group(2), f(m.group(3)), f(m.group(4))


def parse_v7_b1(txt):
    m = re.search(r'for (London|Fergus|Harrow) station index (\S+) .*?an observed shift \(Δobs\) of (\S+), a model minimum \(Δmin\) of (\S+) and a model maximum \(Δmax\) of (\S+), with the inequality test .*? recorded as (TRUE|FALSE), a historical validation outcome of (Bounded|Unbounded|Sign Reversal)', txt)
    if not m:
        return None
    g = m.groups()
    return g[0], g[1], float(g[2]), float(g[3]), float(g[4].rstrip(',')), g[5] == 'TRUE', g[6]


def parse_v7_c1(txt):
    m = re.search(r'for (London|Fergus|Harrow) station index (\S+) the Historical', txt)
    if not m:
        return None
    ents = re.findall(r'"([-\d.]+) \(([-\d.]+) to ([-\d.]+)\) \[Outliers: (\d+)\]"', txt)
    shift = re.search(r'printed as "([^"]+)"\.', txt)
    return m.group(1), m.group(2), [tuple(float(x) for x in e) for e in ents], shift.group(1) if shift else None


def parse_v7_t5(txt):
    m = re.search(r'In Table 5, (\S+) \(.*?\) was (Bounded|Unbounded|Sign Reversal) at London, (Bounded|Unbounded|Sign Reversal) at Fergus and (Bounded|Unbounded|Sign Reversal) at Harrow, with (.*?), because', txt)
    if not m:
        return None
    return m.group(1), {'London': m.group(2), 'Fergus': m.group(3), 'Harrow': m.group(4)}, m.group(5)
