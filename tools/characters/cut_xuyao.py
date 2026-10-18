# 把许遥四视图设定图切成四张透明 PNG：assets/characters/xuyao/{front,left,right,back}.png
# 运行：python tools/characters/cut_xuyao.py     依赖：Pillow、numpy、scipy
# 设定图是纯黑底、人物带深色描边，所以只从图边缘泛洪接近 0 的像素当背景，头发和深色裤子才不会被抠掉
import os, numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'assets', 'characters', 'xuyao-turnaround.jpg')
OUT = os.path.join(ROOT, 'assets', 'characters', 'xuyao')
NAMES = ['front', 'left', 'right', 'back']   # 从左到右：正面、脸朝左、脸朝右、背面

def main():
    os.makedirs(OUT, exist_ok=True)
    a = np.asarray(Image.open(SRC).convert('RGB')).astype(int); H, W, _ = a.shape
    mx = a.max(2)
    lab, _ = nd.label(mx <= 7)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = nd.binary_fill_holes(~np.isin(lab, list(border)))
    # 被身体围住的大块纯黑（两腿之间、腋下）也是背景
    lab2, n2 = nd.label((mx <= 4) & fg)
    for i, s in enumerate(nd.sum(np.ones_like(mx), lab2, range(1, n2 + 1)), 1):
        if s > 150: fg &= ~(lab2 == i)
    fg = nd.binary_opening(fg, iterations=1)
    xs = np.where(fg.any(0))[0]; segs = []; s = p = xs[0]
    for x in xs[1:]:
        if x - p > 8: segs.append((s, p)); s = x
        p = x
    segs.append((s, p)); segs = [g for g in segs if g[1] - g[0] > 40]
    assert len(segs) == 4, segs
    for (x0, x1), nm in zip(segs, NAMES):
        m = np.zeros_like(fg); m[:, x0:x1 + 1] = fg[:, x0:x1 + 1]
        ys = np.where(m.any(1))[0]; y0, y1 = max(0, ys[0] - 2), min(H, ys[-1] + 3)
        al = np.clip((nd.gaussian_filter(m.astype(float), .6) - .15) / .7, 0, 1)
        rgba = np.dstack([a, (al * 255).astype(int)]).astype(np.uint8)[y0:y1, max(0, x0 - 2):min(W, x1 + 3)]
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, nm + '.png'))
        print(nm, rgba.shape[1], rgba.shape[0])

if __name__ == '__main__':
    main()
