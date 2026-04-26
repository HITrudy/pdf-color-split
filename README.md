# PDF Color Splitter

将 PDF 按页拆分为**黑白**和**彩色**两个 PDF 文件。支持 CLI 命令行和 Web 在线服务两种使用方式。

## 功能

- 逐页检测 PDF 内容颜色，自动分类
- 支持截断页数：指定页数之后的内容不检测颜色，直接归入黑白 PDF
- 在线 Web 服务，同一局域网下的设备可通过浏览器上传使用

## 快速开始

### 依赖

```bash
pip install PyMuPDF Pillow Flask
```

### CLI 使用

```bash
cd pdf_check
python3 pdf_check.py input.pdf
```

输出：`input_bw.pdf`（黑白页） + `input_color.pdf`（彩色页）

**可选参数：**

| 参数 | 说明 |
|------|------|
| `-b <file>` | 指定黑白 PDF 输出路径 |
| `-c <file>` | 指定彩色 PDF 输出路径 |
| `-t <num>` | 颜色检测灵敏度 0-255，默认 10，越小越敏感 |
| `-z <float>` | 渲染缩放倍率，默认 1.5，越高越准但越慢 |
| `-n <num>` | 截断页数，此页之后不检测颜色直接归入黑白 |

**示例：**

```bash
# 前 5 页检测颜色，之后直接归黑白
python3 pdf_check.py input.pdf -n 5

# 自定义输出文件名
python3 pdf_check.py input.pdf -b bw.pdf -c color.pdf

# 降低灵敏度，减少误判
python3 pdf_check.py input.pdf -t 30
```

### Web 服务

```bash
cd pdf_check/pdf_check_online
python3 pdf_ckeck_online.py
```

打开浏览器访问 `http://<本机IP>:5000`，同一网络下的设备均可使用。

## 目录结构

```
pdf_check/
├── pdf_check.py                  # CLI 工具 + 核心分类逻辑
├── pdf_check_online/
│   ├── pdf_ckeck_online.py       # Flask Web 服务器
│   ├── templates/
│   │   └── index.html            # Web 上传页面
│   └── uploads/                  # 临时文件目录
└── README.md
```

## 原理

逐页渲染 PDF 为缩略图，遍历像素的 RGB 值。如果任一像素的 RGB 最大分量差超过阈值，判定为彩色页，否则为黑白页。
