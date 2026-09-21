"""Prepare a copy-only local test package, including a prepatched executable."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from exe_delta import apply_delta


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installer', type=Path, help='Bundle the matching installer as a fourth top-level item')
    args = parser.parse_args()
    m = json.loads((args.package / 'manifest.json').read_text(encoding='utf-8'))
    delta = json.loads((args.package / 'exe.delta.json').read_text(encoding='utf-8'))
    original = args.original.read_bytes()
    if digest(original) != m['native']['original_sha256']:
        raise ValueError('Wrong original executable')
    patched = apply_delta(original, delta)
    if digest(patched) != m['native']['patched_sha256']:
        raise ValueError('Patched executable does not match the release')
    game = m['game']
    args.output.mkdir(parents=True, exist_ok=False)
    folder = args.output / (game.upper() + '-手动复制版')
    folder.mkdir()
    expected = {}
    for entry in m['files']:
        rel = Path(entry['path'])
        if rel.is_absolute() or '..' in rel.parts or rel.parts[0] not in ('game', 'root'):
            raise ValueError('Invalid resource path')
        raw = (args.package / rel).read_bytes()
        if len(raw) != entry['size'] or digest(raw) != entry['sha256']:
            raise ValueError('Resource changed: ' + str(rel))
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        expected[rel.as_posix()] = entry['sha256']
    (folder / 'game' / m['exe']).write_bytes(patched)
    expected['game/' + m['exe']] = digest(patched)
    readme = f"""{m['title']} {m['version']} · 手动复制测试版
适用：Windows x64 Steam 版。无需运行安装器或生成工具。

先退出游戏，解压本包。

1. 将 game 文件夹里面的全部 5 个文件复制到本作游戏目录，同名覆盖。
   游戏目录：Steam 右键本作 → 管理 → 浏览本地文件。
   覆盖前请把原 {m['exe']} 复制到其他位置留作备份。

2. 将整个 root 文件夹复制到：
   %LOCALAPPDATA%\\ancr\\{game}\\data
   将上述路径粘贴到资源管理器地址栏即可打开；不存在时自行建立。
   已有 root 时先改名为 root_old（若重名则换个名字），再复制新 root。
   不要动 user 文件夹，里面是存档和个人设置。

3. 从 Steam 启动游戏，在设置里选择中文。

game 中应有这 5 个文件（已全部准备好）：
{m['exe']}
FridaGadget.dll
FridaGadget.config
age2-cn.js
COPYING-frida.txt

本包仅适用于对应篇章及已验证的 Steam 版本，不要复制到其他游戏。
游戏程序已预先应用与当前安装器相同的差分；本包不会自动检查目标游戏版本。
测试包尚未公开发布。
"""
    if args.installer:
        installer_name = game + '-CN-' + m['version'].replace(' ', '-') + '-Setup.exe'
        if args.installer.name != installer_name:
            raise ValueError('Installer filename must match game and version')
        raw = args.installer.read_bytes()
        (folder / installer_name).write_bytes(raw)
        expected[installer_name] = digest(raw)
        readme = f"""{m['title']} 中文补丁 {m['version']}
适用 Windows x64 Steam 版。先退出游戏并完整解压，两种方法任选一种。

【方法一：一键安装】
运行 {installer_name}，选择本作游戏目录，点击安装。
完成后从 Steam 启动游戏，在设置里选择中文。

【方法二：手动安装（安装器打不开时用这个）】
1. 把 game 文件夹里面的全部 5 个文件复制到本作游戏目录，同名覆盖。
   游戏目录：Steam 右键本作 → 管理 → 浏览本地文件。
   覆盖前将原 {m['exe']} 复制到其他位置备份。
2. 把整个 root 文件夹复制到：
   %LOCALAPPDATA%\\ancr\\{game}\\data
   上述路径粘贴到资源管理器地址栏即可打开；不存在时自行建立。
   若已有 root，先改名保留，再复制新 root。不要动 user 文件夹。
3. 从 Steam 启动游戏，在设置里选择中文。

game 中的 5 个文件已准备好，无需运行任何生成工具。
只适用于本作已验证的 Steam 版本，不要混用其他作品或来源的补丁。
手动安装不会自动校验游戏版本；安装器会校验。不确定版本时优先用安装器。

【恢复原版】
先在游戏设置里切回英文或日文，再退出游戏。
将 data\\root 移到备份位置，保留 data\\user；移走游戏目录中的
FridaGadget.dll、FridaGadget.config、age2-cn.js、COPYING-frida.txt。
恢复自己备份的原 EXE（安装器备份在 .age2-cn\\original.exe），
或通过 Steam 验证游戏文件。Steam 验证不会移走 AppData 中的 root。

非官方免费汉化补丁，请使用正版游戏。原作及素材权利归原权利人。
字体和运行组件许可证随对应文件附带。BETA 不代表已完成全部剧情验证。
"""
    (folder / '安装说明.txt').write_text(readme, encoding='utf-8-sig')
    expected['安装说明.txt'] = digest((folder / '安装说明.txt').read_bytes())
    archive = args.output / (game.upper() + '-CN-' + m['version'].replace(' ', '-') + ('-Patch.zip' if args.installer else '-CopyOnly-Test.zip'))
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in expected:
            z.write(folder / name, name)
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == set(expected)
        for name, value in expected.items():
            assert digest(z.read(name)) == value, name
        assert len([n for n in z.namelist() if n.startswith('game/')]) == 5
        top = {'game', 'root', '安装说明.txt'}
        if args.installer:
            top.add(installer_name)
        assert {n.split('/')[0] for n in z.namelist()} == top
    assert digest(args.original.read_bytes()) == m['native']['original_sha256']
    report = {'archive': str(archive.resolve()), 'folder': str(folder.resolve()),
              'original_unchanged': True, 'release_resources_match': True,
              'release_executable_match': True, 'archive_files_verified': len(expected),
              'game_file_count': 5, 'sha256': digest(archive.read_bytes())}
    report['files'] = expected
    (args.output / 'verification-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
