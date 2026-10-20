# 短片制作与素材致谢

以下保留序幕与尾声的原始制作记录。文中源码、字体及目录路径指清理前的制作目录，可从 Git 历史恢复；成片已经内嵌在 `echo.html` 中。

`opening.mp4`、`ending.mp4` 是两段成片按 720p 重新压缩后的版本；`poster.webp` 是序幕第 10.6 秒的画面，用作标题背景。

## 序幕

```
第 47 号磁带 · 开场动画（HD-2D，18 秒）

画面
- 全部由本文件夹里的代码生成：three.js 场景由基本几何体搭成，像素贴图和像素角色（47 的五套装扮、植物、机关）
  逐像素程序绘制（room.js、bot.js），天空、光束、后期都是着色器。没有照片、3D 素材包或 AI 生成图像。
- 故事、角色（47）、场景设计和界面美术均为本片原创。

字体（SIL Open Font License 1.1；只含片中用到的字形的 woff2 子集，取自 Google Fonts；许可证全文在 fonts/）
- Noto Serif SC（思源宋体）：Copyright 2012 Google Inc.，fonts/notoserifsc-sub.woff2，fonts/OFL-NotoSerifSC.txt
- Cinzel：Copyright 2020 The Cinzel Project Authors (https://github.com/NDISCOVER/Cinzel)，fonts/cinzel-sub.woff2，fonts/OFL-Cinzel.txt

音乐
- 原创配乐（music.py），用以下 CC0 采样演奏：竖琴、钟琴、小提琴组、大提琴组（长音 / 拨奏）、低音提琴、圆号、长号、
  定音鼓、大鼓、吊镲、弓奏颤音琴。
  Samples (CC0): VS Chamber Orchestra: Community Edition (Versilian Studios), Versilian Community Sample Library (Versilian Studios)
  https://github.com/sgossner/VSCO-2-CE · https://github.com/sgossner/VCSL

音效与环境声
- 全部在 mix.py 里用程序合成（噪声、滤波、包络），没有录音采样。

代码
- px.js、fx.js、post_ts.js 原样复制自 Lemo-Opuscar 库的 HD-2D 引擎；kit.js 摘自同一引擎。许可证如下（MIT）：

  MIT License

  Copyright (c) 2026 LemoLab

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

- 依赖：three.js r170 (MIT)、playwright-core (Apache-2.0)、numpy / scipy / soundfile (BSD)、ffmpeg (LGPL/GPL)。

参考（只学语法，没有复制任何内容）：HD-2D 类 RPG 的微缩布景画面语言；《双影奇境》在同一构图下切换世界的剪辑方法。
```

## 尾声

```
第 47 号磁带 · 片尾动画（HD-2D，15 秒）

画面
- 全部由本文件夹里的代码生成：three.js 场景由基本几何体搭成，像素贴图、像素角色（47）、草丛、树、救生舱、小屋
  逐像素程序绘制（pod.js、meadow.js、bot.js），舷窗外的地球、天空、后期都是着色器。没有照片、3D 素材包或 AI 生成图像。
- 故事、角色（47、许遥）、场景设计和界面美术均为原创，延续游戏《第 47 号磁带》和它的开场动画。

字体（SIL Open Font License 1.1；只含片中用到的字形的 woff2 子集，取自 Google Fonts；许可证全文在 fonts/）
- Noto Serif SC（思源宋体）：Copyright 2012 Google Inc.，fonts/notoserifsc-sub.woff2，fonts/OFL-NotoSerifSC.txt
- Cinzel：Copyright 2020 The Cinzel Project Authors (https://github.com/NDISCOVER/Cinzel)，fonts/cinzel-sub.woff2，fonts/OFL-Cinzel.txt

音乐
- 原创配乐（music.py），用以下 CC0 采样演奏：竖琴、钟琴、小提琴组、大提琴组、低音提琴、圆号、定音鼓、吊镲、弓奏颤音琴。
  Samples (CC0): VS Chamber Orchestra: Community Edition (Versilian Studios), Versilian Community Sample Library (Versilian Studios)
  https://github.com/sgossner/VSCO-2-CE · https://github.com/sgossner/VCSL

音效与环境声
- 全部在 mix.py 里用程序合成（噪声、滤波、包络），没有录音采样。

代码
- px.js、fx.js、post_ts.js 原样复制自 Lemo-Opuscar 库的 HD-2D 引擎；kit.js 摘自同一引擎；bot.js 来自本片的开场动画
  （新增了背面敲门的两帧）。许可证如下（MIT）：

  MIT License

  Copyright (c) 2026 LemoLab

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

- 依赖：three.js r170 (MIT)、playwright-core (Apache-2.0)、numpy / scipy / soundfile (BSD)、ffmpeg (LGPL/GPL)。

参考（只学语法，没有复制任何内容）：HD-2D 类 RPG 结局演出的微缩外景、点光源打出的影子和升高后拉的收尾。
```
