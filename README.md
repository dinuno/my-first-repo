# 俄罗斯方块 Tetris

一个用 Python + pygame 开发的经典俄罗斯方块游戏，支持旋转、消行计分、等级加速、落点预览等功能，全中文界面。

## 功能特性

- 7 种标准方块 + 随机袋算法（出现均匀）
- 方块旋转（带贴墙自动修正 wall kick）
- 左右移动、软降、空格一键落底
- 落点虚影预览 + 下一个方块预览
- 消行计分（1~4 行分别 100/300/500/800 分，随等级翻倍）
- 每消除 10 行升一级，下落速度递增
- 暂停 / 重新开始 / 游戏结束提示
- 全中文界面

## 快速开始

### 环境要求

- Python 3.8 及以上（推荐 3.12）
- pygame 2.6.1

### 安装依赖

```bash
pip install pygame
```

### 运行游戏

```bash
python tetris.py
```

## 操作说明

| 按键 | 功能 |
|------|------|
| ← → | 左右移动 |
| ↑ / X | 旋转方块 |
| ↓ | 加速下落 |
| 空格 | 直接落底 |
| P | 暂停 / 继续 |
| R | 重新开始 |

## 打包为 Windows 可执行文件

如需生成可独立运行的 `.exe`（无需安装 Python）：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "俄罗斯方块" --clean --noconfirm tetris.py
```

生成的可执行文件位于 `dist/俄罗斯方块.exe`。

## 用 VSCode 打开

项目已附带 `俄罗斯方块.code-workspace` 工作区配置，执行：

```bash
code 俄罗斯方块.code-workspace
```

或直接打开 `tetris.py` 源码。

## 项目结构

```
.
├── tetris.py                  # 游戏主程序源码
├── README.md                  # 项目说明
├── requirements.txt           # 依赖清单
└── 俄罗斯方块.code-workspace  # VSCode 工作区配置
```
