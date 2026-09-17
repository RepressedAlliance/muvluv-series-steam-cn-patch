# AGE2 独立中文运行时

本目录保存 Steam 帝都燃烧与 TDA00–03 的版本专用运行时源码。
截至 2026-09-17，本地五部运行文件已集成中文语言、资源选择、正文排版、
字体缓存与存档摘要修正；这不是五部全路线实机验收声明。

## 加载流程

`tools/runtime/pe_loader.py` 在本地原版 x64 EXE 中增加 Frida Gadget 导入及
初始化等待入口。Gadget 的配置加载生成的 `age2-cn.js`；脚本安装挂钩后设置
就绪标记，入口再进入原程序。初始化超时会提示并退出，不带病进入游戏。
玩家不需要浏览器、Python 或 Frida 命令行。

`tools/runtime/exe_delta.py` 生成并验证程序差分，安装器检查原版与结果的哈希。
原版 EXE、Gadget DLL、商业游戏资源与字体不随源码提交。生成的差分和安装包
也是本地构建产物。挂钩使用固定 RVA，不得直接用于未知版本。

## 各层的中文标识

| 层级 | 中文标识 | 实现 |
| --- | --- | --- |
| 游戏语言 | 9 | 放行语言编号，菜单映射 Auto / EN / JP / CN |
| EGPACK 正文 | `zh_hans` | TDA 使用原生多语言字段；帝都额外保有中文字符串 |
| 菜单图片 | `_zh` | 需同时准备图片与 GUI 资源声明，支持切回日英 |
| 剧情图片 | `_ck` | 修正独立的剧情图片语言选择入口 |
| 字体配置 | `Font_cn.cfg` | 仅在中文模式条件选择，保留日英配置 |
| 存档摘要键 | `ck` | 简中 9 的序列化键；不能使用会被读成 8 的 `zh` |

松散资源仍放在 `%LOCALAPPDATA%/ancr/<game>/data/root`。
仅放置文件不会自动创建上述语言通道。`build_script.py` 组合基础模块、各作挂钩、
存档摘要、TDA GUI 字体缓存以及正文排版模块。

## 正文与字体

- 正文自动换行仍使用引擎显示链路，在其基础上调整中文分片与分行选择。
  TDA01–03 的普通正文另有针对已选字体标定的布局规划；复杂控制符、注音、
  多记录及不匹配的几何条件走保守分支，不把普通句模型套用到所有节点。
- `body_layout` 中的字宽数据与当前可可体 Bold 对应，换字体后不能直接声称标定仍有效。
- EGPACK 的字面 `\n` 与真实 CR/LF 不同。默认拒绝手动换行；原文同数量保留或
  逐项 `line_break_reason` 审定的中文正文可使用字面 `\n`。写回与重新解析通过
  不等于该位置的视觉布局已实测。普通正文不逐句添加强制换行。
- 中文沿用原版 CJK 字号选择，避免误用英文尺寸；帝都修正字体/高度变化后
  父节点位置未刷新的裁切问题。
- `tda_gui_locale.js` 在语言改变时使同文节点重新生成文字纹理，解决“音量”等
  中日相同文字仍沿用启动语言字体的问题。

当前选字：正文白无常可可体 Bold，角色名美呗嘿嘿体 3.0，系统 IBM Plex Sans SC Regular。
字库与补字二进制不在本目录；免费商用声明与开源许可应分别核实，不能混用概念。

## 存档摘要修正

`save_preview.js` 修正两个独立问题：原生摘要生成只遍历 JP/EN，增加 CN=9；
原生写入把 9 写成 `zh`，读取却将其识别为 8，因此只在摘要写入调用点改成 `ck`。
不更改全局图片后缀，不修改玩家存档结构。此前没有中文摘要的旧档需载入后重新保存。

已用正式脚本在 TDA01 新空槽保存、完全退出并重启，确认中文姓名和台词摘要仍显示。
另外四部已适配、部署并检查包，未逐部进行这项保存/重启实机验证。

## 验证边界

五部脚本与安装包已有离线检查；TDA03 语言切换字体刷新和 TDA01 摘要已有针对性
实机记录，帝都正文位置刷新也做过实机复查。用户持续浏览正文暂未发现明显排版错误。
这些证据不覆盖每句、每张图或所有语言切换方向。Log 分段、缓存及细线显示的进一步
比对留待独立复核，不以改变原作行为为默认目标。

## 可复用入口

- `../tools/runtime/build_script.py`：`build_script(game, ready_rva, hooks)`，其中
  `ready_rva` 来自 `embed_runtime` 的返回元数据，不能任意填写。
- `../tools/runtime/build_installers.py`：从已有、已审定 staging 构建安装器。
- `../tools/runtime/verify_release_resources.py --help`：按提取的原版检查语言隔离。
- `../packaging/windows/README.md`：安装器布局、备份与失败恢复。
- `../tools/images/`：保留原英文主体的 UI 副标题、字幕、说明与语音标签绘制。

仓库提供技术组件，不包含一键重建所有最终图片和字体所需的私有输入及全部本地
研究脚本。不要把源码公开等同于已发布新的玩家补丁。

在仓库根目录运行：

```powershell
python -m unittest discover -s AGE2/tests -p "test_*.py"
node AGE2/tests/packaging/test_gui_locale_cache.cjs
python AGE2/tests/packaging/run_install_engine_tests.py
```

最后一项需要 Windows .NET Framework 编译器，会自行编译测试程序，只操作新建的
合成游戏目录，不接触 Steam 安装或真实存档。PE 构建的额外依赖见
`../tools/runtime/requirements.txt`；运行与再分发 Gadget 时另遵守其上游许可。
