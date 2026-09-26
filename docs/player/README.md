# 玩家下载、安装、卸载与排错指南

[返回首页](../../README.md) · [English](../en/player-guide.md) · [研究与制作入口](../research/README.md) · [提交 Bug](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/issues/new?template=bug-report.yml)

## AGE2 BETA · 安装方式更新 2026-09-21

| 游戏 | 版本 | 下载 |
| --- | --- | --- |
| TDA00 | **BETA 0.2.1** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda00-BETA-0.2.1/TDA00-CN-BETA-0.2.1-Complete.zip) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda00-BETA-0.2.1) |
| TDA01 | **BETA 0.3.3** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda01-BETA-0.3.3/TDA01-CN-BETA-0.3.3-Patch.zip) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda01-BETA-0.3.3) |
| TDA02 | **BETA 0.2.1** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda02-BETA-0.2.1/TDA02-CN-BETA-0.2.1-Patch.zip) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda02-BETA-0.2.1) |
| TDA03 | **BETA 0.2.7** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/tda03-BETA-0.2.7/TDA03-CN-BETA-0.2.7-Patch.zip) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/tda03-BETA-0.2.7) |
| 帝都燃烧篇 | **BETA 0.2.1** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/imperial-capital-burns-BETA-0.2.1/TM-CN-BETA-0.2.1-Patch.zip) · [发布说明](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/imperial-capital-burns-BETA-0.2.1) |

五部作品都提供一键安装和手动复制。解压后只有四项：`安装说明.txt`、`root`、`game` 和安装器。

**一键安装：**退出游戏 → 运行安装器 → 选择本作目录 → 安装。

**手动安装：**退出游戏并备份原 EXE，将 `game` 里的五个文件复制到本作游戏目录，同名覆盖；将整个 `root` 复制到下表位置。已有 `root` 先改名保留，**不要动 `user`**。无需运行生成工具。

| 游戏 | root 放到这里 |
| --- | --- |
| TDA00 | `%LOCALAPPDATA%\ancr\tda00\data` |
| TDA01 | `%LOCALAPPDATA%\ancr\tda01\data` |
| TDA02 | `%LOCALAPPDATA%\ancr\tda02\data` |
| TDA03 | `%LOCALAPPDATA%\ancr\tda03\data` |
| 帝都燃烧 | `%LOCALAPPDATA%\ancr\tm\data` |

安装后从 Steam 启动游戏，在设置里选择中文。本次汉化内容不变，已正常安装上一版无需重装。

恢复原版：先切回英文或日文，再退出游戏。保留 `data/user`，将 `data/root` 和游戏目录中的 `FridaGadget.dll`、`FridaGadget.config`、`age2-cn.js`、`COPYING-frida.txt` 移到备份位置；恢复自行备份的原 EXE（安装器备份为 `.age2-cn/original.exe`），或用 Steam 验证恢复程序。Steam 验证不会移走 AppData 的补丁资源。

旧 ZIP 的安装与恢复说明见[历史版本说明](historical-age2.md)，不适用于新版安装器。

## 玩家下载

### 光子之花 / 光子旋律

光子之花、光子旋律已正式公开发布，各自下载、安装，不混用。以下是 Windows / Steam 的完整简体中文补丁：

| 游戏 | 版本 | 下载 |
| --- | --- | --- |
| Muv-Luv 光子之花 | **BETA 0.1.2** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/pf-BETA-0.1.2/MuvLuv_PF_CN_Patch_BETA_0.1.2.zip) · [发布页](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/pf-BETA-0.1.2) |
| Muv-Luv 光子旋律 | **BETA 0.1.2** | [下载汉化补丁](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/download/pm-BETA-0.1.2/MuvLuv_PM_CN_Patch_BETA_0.1.2.zip) · [发布页](https://github.com/RepressedAlliance/muvluv-series-steam-cn-patch/releases/tag/pm-BETA-0.1.2) |

Steam 语言设为 **English（英语）**，等待下载完成并退出游戏；解压 ZIP，双击 EXE，点击“安装汉化”。无需安装旧版，也无需手动运行校验脚本。安装器自动定位游戏目录，未找到时选择对应文件夹。

**BETA 0.1.2** 同步最新校对：光子之花 24 条、光子旋律 23 条。校对及反馈致谢：**柚子コショウ**。两款均保留 BETA 0.1.1 修复，可从旧版直接覆盖升级。光子之花偶发英文及光子旋律《再诞》片尾动画英文尚未解决；详见[更新范围与署名](../project/photon-beta012-proofreading.md)。

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
