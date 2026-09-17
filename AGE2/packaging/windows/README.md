# AGE2 Windows 安装程序

每部作品生成一个内嵌资源的 Windows x64 EXE。界面沿用 PM/PF 安装程序的目录选择方式，识别 Steam 库中的对应游戏；执行引擎直接使用 .NET，不依赖玩家安装 Python、Frida 命令行或 PowerShell 7。

安装引擎先验证包内文件和原游戏 EXE 版本，生成该版本的程序差分结果，然后准备完整的新 `root`。准备完成后才切换活动目录，安装中文资源、三份基础文件与运行组件。游戏运行时拒绝安装。

原 `root` 移入本作 `data/.age2-cn-backups/<事务号>/root`，原程序保存在游戏目录 `.age2-cn/original.exe`；逐次被替换的程序文件与安装记录保存在 `.age2-cn/transactions/<事务号>`。失败恢复也保留诊断文件。此流程不会删除 `data/user`，也不删除玩家存档；旧覆盖资源仍作为副本保留，不再参与游戏读取。

安装过程中遇到链接目录、版本不符、包文件损坏、过长的资源路径或文件锁定，会停止或恢复安装前状态。当前实现的事务恢复已用模拟目录及五部完整资源包测试，未在玩家真实安装目录执行。

构建命令：

```powershell
python AGE2/tools/runtime/build_installers.py --staging <五部候选包目录> --output <新的输出目录>
```

输入采用 `age2-cn-package-1` 清单和 `age2-exe-delta-1` 差分。构建需要 Windows 自带的 .NET Framework C# 编译器。`--inspect <报告路径>` 只展开包并检查安装界面／目录识别，不执行安装，保留展开目录供复核。

当前产物标注“验收版”。安装程序通过不代表内容翻译、全部场景和语言切换均已验收；内容状态以五部修订记录为准。
