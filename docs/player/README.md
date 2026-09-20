# 玩家下载、安装、卸载与排错指南

[返回首页](../../README.md) · [English](../en/player-guide.md) · [研究与制作入口](../research/README.md) · [提交 Bug](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/issues/new?template=bug-report.yml)

## AGE2 BETA · 2026-09-20

| 游戏 | 版本 | 下载 |
| --- | --- | --- |
| TDA00 | **BETA 0.2.0** | [安装程序 EXE](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda00-BETA-0.2.0/tda00-CN-BETA-0.2.0-Setup.exe) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda00-BETA-0.2.0) |
| TDA01 | **BETA 0.3.2** | [安装程序 EXE](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda01-BETA-0.3.2/tda01-CN-BETA-0.3.2-Setup.exe) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda01-BETA-0.3.2) |
| TDA02 | **BETA 0.2.0** | [安装程序 EXE](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda02-BETA-0.2.0/tda02-CN-BETA-0.2.0-Setup.exe) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda02-BETA-0.2.0) |
| TDA03 | **BETA 0.2.6** | [安装程序 EXE](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda03-BETA-0.2.6/tda03-CN-BETA-0.2.6-Setup.exe) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda03-BETA-0.2.6) |
| 帝都燃烧篇 | **BETA 0.2.0** | [安装程序 EXE](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/imperial-capital-burns-BETA-0.2.0/tm-CN-BETA-0.2.0-Setup.exe) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/imperial-capital-burns-BETA-0.2.0) |

Windows x64 Steam：退出游戏 → 运行对应 EXE → 安装 → 在游戏设置中选择中文。无需旧补丁。安装器保留旧资源和原程序，不改玩家存档。

恢复：退出游戏，将对应 `ancr/<game>/data/root` 移到备份位置，保留 `data/user`；恢复游戏目录 `.age2-cn/original.exe` 为原 EXE 文件名，并移走本补丁的 `FridaGadget.dll`、`FridaGadget.config`、`age2-cn.js`、`COPYING-frida.txt`。各发布页附具体说明、SHA-256 和资源清单。

旧 ZIP 的安装与恢复说明见[历史版本说明](historical-age2.md)，不适用于新版安装器。

## 玩家下载

### 光子之花 / 光子旋律

光子之花、光子旋律已正式公开发布，各自下载、安装，不混用。以下是 Windows / Steam 的完整简体中文补丁：

| 游戏 | 版本 | 下载 |
| --- | --- | --- |
| Muv-Luv 光子之花 | **BETA 0.1.1** | [ZIP](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/pf-BETA-0.1.1/MuvLuv_PF_CN_Patch_BETA_0.1.1.zip) · [发布页](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/pf-BETA-0.1.1) |
| Muv-Luv 光子旋律 | **BETA 0.1.1** | [ZIP](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/pm-BETA-0.1.1/MuvLuv_PM_CN_Patch_BETA_0.1.1.zip) · [发布页](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/pm-BETA-0.1.1) |

Steam 语言设为 **English（英语）**，等待下载完成并退出游戏；解压 ZIP，双击 EXE，点击“安装汉化”。无需安装旧版，也无需手动运行校验脚本。安装器自动定位游戏目录，未找到时选择对应文件夹。

光子旋律 **BETA 0.1.1** 修复 297 条特殊文本指令，解决部分独白显示日文、重复文字或缺字的问题。已安装光子旋律 BETA 0.1 的玩家可直接覆盖安装，无需先卸载。光子之花 **BETA 0.1.1** 补齐正文及小字注释中的 11 个缺字，修复“首席女伶”“亟待收复”等处的方框；光子之花 BETA 0.1 同样可直接覆盖升级。

采用 R2 内容，并修复回看“返回游戏”按钮。**完全不备份，不附卸载器或回滚程序。** 安装失败、中断或恢复原版时，保留存档，通过 Steam 卸载对应游戏，清除该游戏安装目录中的汉化残留，再重新下载。只处理对应游戏文件夹，不要清空 Steam 根目录、steamapps/common、userdata 或个人存档目录。仅验证完整性不能保证清除额外汉化文件。

## 排错与反馈

请提供游戏名称、补丁版本、Windows 环境、报错截图及前后台词，并说明是否安装其他补丁。
AGE2 在游戏设置中选择中文；光子之花／光子旋律在安装前将 Steam 语言设为 English。
不要混用不同作品的补丁。Steam Deck／Proton 不应视为已经验证的支持平台。

[提交运行问题](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/issues/new?template=bug-report.yml)
· [提交翻译修正](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/issues/new?template=translation-review.yml)
· QQ 交流群：273626767。

## 历史版本

[AGE2 旧 ZIP 安装、恢复与已知问题](historical-age2.md)。历史 Release、tag 和附件保留；新玩家使用本页当前版本。