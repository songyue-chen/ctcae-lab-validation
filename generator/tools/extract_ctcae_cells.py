"""Column-aware CTCAE lab-term extraction from pdftotext -tsv output (word bounding boxes)."""
import sys, csv, json, re
from collections import defaultdict
mode, tsv, termfile, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
terms = [t.strip() for t in open(termfile, encoding='utf-8') if t.strip()]
rows = list(csv.DictReader(open(tsv, encoding='utf-8'), delimiter='\t'))
words = defaultdict(list)   # page -> [(top, left, right, text)]
for r in rows:
    if r['text'] == '###FLOW###' or r['text'] == '###LINE###' or r['text'] == '###PAGE###' or float(r['conf']) < 0: continue
    p = int(r['page_num']); l = float(r['left']); t = float(r['top']); w = float(r['width'])
    words[p].append((t, l, l + w, r['text']))
def lines_of(ws):
    """group words into lines by top coordinate (tolerance 3pt)"""
    ws = sorted(ws, key=lambda x: (round(x[0]), x[1]))
    lines = []
    for wd in ws:
        if lines and abs(lines[-1][0] - wd[0]) <= 3: lines[-1][1].append(wd)
        else: lines.append([wd[0], [wd]])
    return [(top, sorted(ws_, key=lambda x: x[1])) for top, ws_ in lines]
def text(ws): return re.sub(r'\s+', ' ', ' '.join(w[3] for w in sorted(ws, key=lambda x: (round(x[0]), x[1])))).strip()
res = []
for p in sorted(words):
    L = lines_of(words[p])
    ltext = [text(ws) for _, ws in L]
    if mode == 'v6':
        # page number: first line that is a bare integer
        pp = next((int(t) for t in ltext[:3] if re.fullmatch(r'\d{1,3}', t)), None)
        i = 0
        while i < len(L):
            hit = next((t for t in terms if ltext[i].lower() == t.lower()), None)
            if hit and i + 1 < len(L) and ltext[i+1].startswith('Grade 1'):
                hdr = L[i+1][1]
                starts = [w[1] for w in hdr if w[3] == 'Grade']
                if len(starts) != 5: print('WARN header', p, hit, starts); i += 1; continue
                cells = [[] for _ in range(5)]
                j = i + 2
                while j < len(L) and not ltext[j].startswith('Definition:'):
                    for wd in L[j][1]:
                        k = max(c for c in range(5) if wd[1] >= starts[c] - 4)
                        cells[k].append(wd)
                    j += 1
                defn = []
                while j < len(L) and not ltext[j].startswith('Navigational Note'):
                    defn.append(ltext[j]); j += 1
                nav = [ltext[j]] if j < len(L) else []
                j += 1
                while j < len(L) and not any(ltext[j].lower() == t.lower() for t in terms) and not ltext[j].startswith('Grade 1') and not re.fullmatch(r'CTCAE v6\.0|\d{1,3}', ltext[j]) and L[j][1][0][1] < 60 and not ltext[j][0].isupper() or (j < len(L) and ltext[j].startswith('specify')):
                    nav.append(ltext[j]); j += 1
                res.append({'version': 6, 'term': hit, 'page': pp, 'pdf_page': p,
                            'grades': {str(g+1): text(cells[g]) for g in range(5)},
                            'definition': ' '.join(defn).replace('Definition: ', '', 1),
                            'nav': ' '.join(nav).replace('Navigational Note: ', '', 1)})
                i = j; continue
            i += 1
    else:
        if not any(t.startswith('CTCAE Term') for t in ltext): continue
        pp = next((int(m.group(1)) for t in ltext for m in [re.search(r'Page (\d+)$', t)] if m), None)
        hidx = next(k for k, t in enumerate(ltext) if t.startswith('CTCAE Term'))
        # column starts from run-start words (first word of a line, or gap > 6pt before it) in the body
        body = [k for k in range(hidx + 1, len(L)) if not ltext[k].startswith(('Definition:', 'Navigational Note', 'CTCAE v5.0'))]
        from collections import Counter
        cnt = Counter()
        for k in body:
            ws = L[k][1]
            prev_right = -100
            for wd in ws:
                if wd[1] - prev_right > 6: cnt[round(wd[1])] += 1
                prev_right = wd[2]
        pos = sorted(x for x, c in cnt.items() if c >= 2)
        clusters = []
        for x in pos:
            if clusters and x - clusters[-1][-1] <= 4: clusters[-1].append(x)
            else: clusters.append([x])
        starts = [min(c) for c in clusters]
        if len(starts) != 6:
            # keep the 5 largest clusters right of the term column plus the term column
            sc = sorted(clusters, key=lambda c: -sum(cnt[x] for x in c))
            keep = sorted(min(c) for c in sc[:6])
            starts = keep
        if len(starts) != 6: print('WARN cols', p, pp, starts); continue
        k = hidx + 1
        while k < len(L):
            ws = L[k][1]
            first_left = ws[0][1]
            if first_left < starts[1] - 4 and not ltext[k].startswith(('Definition:', 'Navigational Note', 'CTCAE v5.0')) and any(wd[1] >= starts[1] - 4 for wd in ws):
                cells = [[] for _ in range(6)]
                j = k
                while j < len(L) and not ltext[j].startswith('Definition:'):
                    for wd in L[j][1]:
                        c = max(cc for cc in range(6) if wd[1] >= starts[cc] - 4)
                        cells[c].append(wd)
                    j += 1
                defn = []
                while j < len(L) and not ltext[j].startswith('Navigational Note'):
                    defn.append(ltext[j]); j += 1
                nav = [ltext[j]] if j < len(L) else []
                j += 1
                term = text(cells[0])
                hit = next((t for t in terms if term.lower() == t.lower()), None)
                if hit:
                    res.append({'version': 5, 'term': hit, 'page': pp, 'pdf_page': p,
                                'grades': {str(g): text(cells[g]) for g in range(1, 6)},
                                'definition': ' '.join(defn).replace('Definition: ', '', 1),
                                'nav': ' '.join(nav).replace('Navigational Note: ', '', 1)})
                k = j; continue
            k += 1
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
seen = [r['term'] for r in res]
for r in res:
    print(f"\n### v{r['version']} | {r['term']} | p.{r['page']}")
    for g in '12345': print(f"  G{g}: {r['grades'][g]}")
    if r['nav'] not in ('-', ''): print(f"  NAV: {r['nav']}")
print('\n##### not found:', [t for t in terms if t not in seen])
print('##### duplicates:', [t for t in set(seen) if seen.count(t) > 1])
