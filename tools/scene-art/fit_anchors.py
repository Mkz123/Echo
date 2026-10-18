# 场景整景与逻辑格子对齐：给每张背景里每个可走格子算出它在画面上的中心位置。
# 玩法格子不变；只移动"这个格子画在哪里"，让 47 站在画出来的路上。
# 运行：python tools/scene-art/fit_anchors.py [--review DIR]
# 依赖：Pillow、numpy、scipy
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import uniform_filter, gaussian_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BG = os.path.join(ROOT, 'assets', 'backgrounds-v3')
OUT = os.path.join(ROOT, 'tools', 'scene-art', 'anchors.json')
OVR = os.path.join(ROOT, 'tools', 'scene-art', 'overrides.json')
S = 24                 # 分析分辨率：每格像素
R = 0.55               # 最多偏移半格多一点
STEP = 1 / 12
BOX = 0.5              # 打分用的方框边长（格）：比格子小，房间边缘的格子不会被墙推向中间
LAM, MU = 0.35, 3.0    # 偏离原位的代价、相邻格偏移不一致的代价（大：一条路/一个房间整体平移，不会各格乱抖）

levels = json.load(open(os.path.join(BG, 'layouts.json')))['levels']
entries = json.load(open(os.path.join(BG, 'manifest.json')))['entries']
overrides = json.load(open(OVR)) if os.path.exists(OVR) else {}

def features(im):
    a = np.asarray(im, dtype=np.float32) / 255
    g = a.mean(2)
    sd = np.sqrt(np.maximum(0, uniform_filter(g * g, 5) - uniform_filter(g, 5) ** 2))
    q = np.clip((a * 12).astype(int), 0, 11)
    t = np.clip((sd / 0.06 * 4).astype(int), 0, 3)    # 地面平整，机器和叶子纹理多
    return ((q[..., 0] * 12 + q[..., 1]) * 12 + q[..., 2]) * 4 + t

def floor_prob(F, pos, neg):
    nb = 12 * 12 * 12 * 4
    hp = np.bincount(F[pos], minlength=nb).astype(float); hn = np.bincount(F[neg], minlength=nb).astype(float)
    hp = gaussian_filter(hp.reshape(12, 12, 12, 4), (.7, .7, .7, .4)).ravel(); hn = gaussian_filter(hn.reshape(12, 12, 12, 4), (.7, .7, .7, .4)).ravel()
    hp /= hp.sum(); hn /= hn.sum()
    p = hp / (hp + hn + 1e-12)
    return gaussian_filter(p[F], S * .12)

def masks(walk, off, H, W):
    pos = np.zeros((H, W), bool); neg = np.zeros((H, W), bool)
    h, w = walk.shape
    for y in range(h):
        for x in range(w):
            if walk[y, x]:
                dx, dy = off.get((x, y), (0, 0))
                cx, cy = (x + .5 + dx) * S, (y + .5 + dy) * S; r = S * .22
                pos[int(cy - r):int(cy + r), int(cx - r):int(cx + r)] = True
            else:
                near = any(0 <= x + i < w and 0 <= y + j < h and walk[y + j, x + i] for i in (-1, 0, 1) for j in (-1, 0, 1))
                m = .15 if not near else .3     # 挨着路的墙格只取中间，避免把画偏的路当墙
                neg[int((y + m) * S):int((y + 1 - m) * S), int((x + m) * S):int((x + 1 - m) * S)] = True
    return pos, neg

def box_mean(P):
    k = int(BOX * S)
    return uniform_filter(P, k, mode='constant')

def fit(walk, P, prior):
    h, w = walk.shape
    B = box_mean(P)
    cand = np.arange(-R, R + 1e-9, STEP)
    cells = [(x, y) for y in range(h) for x in range(w) if walk[y, x]]
    unary = {}
    for (x, y) in cells:
        U = np.zeros((len(cand), len(cand)))
        bx, by = prior.get((x, y), (0, 0)); sc = .3 if (x, y) in prior else 1   # 手工定位的格子只做小范围微调
        for j, dy in enumerate(cand):
            for i, dx in enumerate(cand):
                px, py = int((x + .5 + bx + dx * sc) * S), int((y + .5 + by + dy * sc) * S)
                v = B[min(max(py, 0), B.shape[0] - 1), min(max(px, 0), B.shape[1] - 1)]
                U[j, i] = v - LAM * (dx * dx + dy * dy)
        unary[(x, y)] = U
    # off = 相对于先验位置的偏移；相邻格的偏移要一致，所以手工压缩过的一段路会整体保持间距
    off = {c: (0.0, 0.0) for c in cells}
    for c in cells:
        j, i = np.unravel_index(np.argmax(unary[c]), unary[c].shape); off[c] = (cand[i], cand[j])
    DX, DY = np.meshgrid(cand, cand)
    for _ in range(12):
        for (x, y) in cells:
            tot = unary[(x, y)].copy()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in off:
                    ox, oy = off[(nx, ny)]; tot -= MU * ((DX - ox) ** 2 + (DY - oy) ** 2)
            j, i = np.unravel_index(np.argmax(tot), tot.shape); off[(x, y)] = (cand[i], cand[j])
    res = {}
    for c, (dx, dy) in off.items():
        bx, by = prior.get(c, (0, 0)); sc = .3 if c in prior else 1
        res[c] = (bx + dx * sc, by + dy * sc)
    return res

def seg_score(P, a, b):
    n = 16; v = []
    for t in np.linspace(0, 1, n):
        px, py = (a[0] + (b[0] - a[0]) * t) * S, (a[1] + (b[1] - a[1]) * t) * S
        v.append(P[min(int(py), P.shape[0] - 1), min(int(px), P.shape[1] - 1)])
    return float(np.min(gaussian_filter(np.array(v), 1)))

def run(review=None):
    result, report, seen = {}, [], set()
    for e in entries:
        k = e['key']
        if k in seen: continue
        seen.add(k)
        lv = levels[e['level'] - 1]; mp = lv['map']; h, w = lv['height'], lv['width']
        walk = np.array([[c != '#' for c in row] for row in mp])
        im = Image.open(os.path.join(BG, e['png'])).convert('RGB').resize((w * S, h * S), Image.LANCZOS)
        F = features(im)
        # 手工定位：画面坐标（格为单位，1.5 = 第 1 列中心），用于画面比地图挤压或错开超过半格的地方
        prior = {}
        for c, v in overrides.get(k, {}).items():
            if c.startswith('_'): continue
            x, y = map(int, c.split(',')); prior[(x, y)] = (v[0] - x - .5, v[1] - y - .5)
        off = {}
        for it in range(3):     # 用上一轮拟合的位置重新采样地面颜色
            pos, neg = masks(walk, off, h * S, w * S)
            P = floor_prob(F, pos, neg)
            off = fit(walk, P, prior)
        cen = {c: (c[0] + .5 + d[0], c[1] + .5 + d[1]) for c, d in off.items()}
        B = box_mean(P)
        cs = {c: float(B[int(p[1] * S), int(p[0] * S)]) for c, p in cen.items()}
        es = {}
        for (x, y), p in cen.items():
            for q in ((x + 1, y), (x, y + 1)):
                if q in cen: es[((x, y), q)] = seg_score(P, p, cen[q])
        result[k] = {'w': w, 'h': h, 'cells': {f'{x},{y}': [round(p[0] / w, 5), round(p[1] / h, 5)] for (x, y), p in sorted(cen.items())}}
        weak_c = [f'{c[0]},{c[1]}:{v:.2f}' for c, v in cs.items() if v < .55]
        weak_e = [f'{a[0]},{a[1]}-{b[0]},{b[1]}:{v:.2f}' for (a, b), v in es.items() if v < .4]
        moved = max(max(abs(d[0]), abs(d[1])) for d in off.values())
        jit = max([abs(cen[b][0] - cen[a][0] - (b[0] - a[0])) + abs(cen[b][1] - cen[a][1] - (b[1] - a[1])) for (a, b) in es] or [0])
        pts = np.array(list(cen.values())); dd = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(-1)) + np.eye(len(pts)) * 9
        report.append(f'{k:15s} maxshift {moved:.2f} jitter {jit:.2f} mindist {dd.min():.2f}  weakcells {weak_c}  weakedges {weak_e}')
        if review:
            draw_review(review, k, e, lv, cen, cs, es, P)
    json.dump(result, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
    print('\n'.join(report)); print('→', OUT)

def draw_review(dirp, k, e, lv, cen, cs, es, P):
    os.makedirs(dirp, exist_ok=True)
    w, h = lv['width'], lv['height']; Z = 64
    im = Image.open(os.path.join(BG, e['png'])).convert('RGB').resize((w * Z, h * Z), Image.LANCZOS)
    d = ImageDraw.Draw(im, 'RGBA')
    for (a, b), v in es.items():
        col = (0, 255, 120, 255) if v >= .4 else (255, 40, 40, 255)
        d.line([cen[a][0] * Z, cen[a][1] * Z, cen[b][0] * Z, cen[b][1] * Z], fill=col, width=3)
    for c, p in cen.items():
        x, y = p[0] * Z, p[1] * Z; r = Z * .4
        col = (0, 255, 120, 220) if cs[c] >= .55 else (255, 60, 60, 240)
        d.rectangle([x - r, y - r, x + r, y + r], outline=col, width=2)
        ch = lv['map'][c[1]][c[0]]
        if ch != '.': d.text((x - r + 3, y - r + 2), ch, fill=(255, 255, 0, 255))
        d.text((x - 10, y + r - 13), f'{c[0]},{c[1]}', fill=(255, 255, 255, 200))
    for i in range(w * 2 + 1): d.line([i * Z / 2, 0, i * Z / 2, 6], fill=(255, 255, 255, 160), width=1)
    for j in range(h * 2 + 1): d.line([0, j * Z / 2, 6, j * Z / 2], fill=(255, 255, 255, 160), width=1)
    im.save(os.path.join(dirp, k + '.jpg'), quality=80)

if __name__ == '__main__':  # noqa
    rv = sys.argv[sys.argv.index('--review') + 1] if '--review' in sys.argv else None
    run(rv)
