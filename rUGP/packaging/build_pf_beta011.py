"""Build PF BETA 0.1.1 from the public BETA 0.1 ZIP and a locked OFL donor."""
from pathlib import Path
import argparse
import copy
import datetime
import hashlib
import io
import json
import shutil
import zipfile

from localization.tools.extend_font_subset import extend
from rUGP.packaging import build_photon_cn_beta01 as ab
from rUGP.packaging.build_photon_player import write_json
from rUGP.packaging.build_player_exe import build
from rUGP.tools.runtime.rebind_photon_font import rebind

OLD_ZIP = 'E8933FAB8D3E4285A82269653B3F58D738BA6B2803BC2C96B956D5D148EFCCC3'
OLD_FONT = 'AADF895003AE6452E1FBDCA1B64206B77D6F9A6EEBE226C31D46D1247AD4830B'
NEW_FONT = '938A0046459DECF03FC11DC4D7FB9D440287EBE162C2F55F5964FAE661B0EC64'
OLD_DLL = '80F311F3AC8FAEA4612C779CAF718E238FE0ACAADB8CB739A4917D8C44AFB684'
NEW_DLL = 'E7F3B5D1D3E6B63CBD2E69CA408C820FBBE5644DE4A371B49626F6EF1A06A9EC'
DONOR = '763146584CF0710223441356B4395E279021B0806C196614377A7A0174AE074A'
ADDED = '亟伶抉捆涟淀漪箍绎菊诘'


def build_release(old_zip: Path, donor: Path, output: Path, csc: Path):
    if ab.sha256(old_zip) != OLD_ZIP:
        raise ValueError('Expected the exact public PF BETA 0.1 ZIP')
    output.mkdir(parents=True, exist_ok=False)
    package = output / 'package'
    package.mkdir()
    with zipfile.ZipFile(old_zip) as outer:
        old_readme = outer.read('使用说明.txt').decode('utf-8-sig').replace('\r\n', '\n')
        with zipfile.ZipFile(io.BytesIO(outer.read('PF_汉化补丁_BETA_0.1.exe'))) as inner:
            for name in inner.namelist():
                if name.startswith(('/', '\\')) or '..' in Path(name).parts:
                    raise ValueError('Unsafe archive member')
            inner.extractall(package)
    before_hashes = {p.relative_to(package).as_posix(): ab.sha256(p)
                     for p in package.rglob('*') if p.is_file()}
    mp = package / 'package_manifest.20260910.json'
    manifest = json.loads(mp.read_text(encoding='utf8'))
    before = copy.deepcopy(manifest)
    assert manifest['game'] == 'PF' and manifest['backup_policy'] == 'none'
    font, font_report = extend((package / 'files/PhotonR2-Regular.ttf').read_bytes(),
                               donor.read_bytes(), ADDED, OLD_FONT, DONOR, 400)
    digest = lambda data: hashlib.sha256(data).hexdigest().upper()
    assert digest(font) == NEW_FONT
    runtime, runtime_report = rebind((package / 'files/Ages3ResT.dll').read_bytes(),
                                     OLD_DLL, OLD_FONT, NEW_FONT)
    assert digest(runtime) == NEW_DLL
    for target, data in [('PhotonR2-Regular.ttf', font), ('Ages3ResT.dll', runtime)]:
        row = next(f for f in manifest['files'] if f['target'] == target)
        old = row['payload']
        accepted = dict(exists=True, bytes=old['bytes'], sha256=old['sha256'])
        if accepted not in row['accepted_bases']:
            row['accepted_bases'].append(accepted)
        path = package / old['path']
        path.write_bytes(data)
        row['payload'] = ab.artifact(path, package)
    assert manifest['archives'] == before['archives']
    manifest['version'] = 'BETA 0.1.1'
    manifest['build_id'] = '2026.09.14-r4'
    write_json(mp, manifest)
    sp = package / 'package_seal.20260910.json'
    seal = json.loads(sp.read_text(encoding='utf8'))
    seal['manifest'] = ab.artifact(mp, package)
    write_json(sp, seal)
    changed = [name for name, value in before_hashes.items() if ab.sha256(package / name) != value]
    assert set(changed) == {'files/PhotonR2-Regular.ttf', 'files/Ages3ResT.dll', mp.name, sp.name}
    write_json(output / 'font-build.json', font_report)
    write_json(output / 'runtime-rebind.json', runtime_report)
    ab.BUILD_EPOCH = int(datetime.datetime(2026, 9, 14, tzinfo=datetime.timezone.utc).timestamp())
    player = output / 'player'
    player.mkdir()
    exe = player / 'PF_汉化补丁_BETA_0.1.1.exe'
    report = build(package, exe, output / 'build', csc)
    second = output / 'second/package'
    shutil.copytree(package, second)
    report2 = build(second, output / 'second/PF.exe', output / 'second/build', csc)
    assert report['payload_sha256'] == report2['payload_sha256']
    readme = old_readme.replace('简体中文补丁 BETA 0.1\n', '简体中文补丁 BETA 0.1.1\n')
    readme = readme.replace('PF_汉化补丁_BETA_0.1.exe', exe.name)
    readme = readme.replace('本版内容\n', '本版内容\n补齐正文和小字注释所需的 11 个缺失汉字，修复“首席女伶”“亟待收复”等处的方框。\n已安装 PF BETA 0.1 的玩家可直接覆盖安装，无需先卸载，不改动个人存档。\n')
    readme = readme.replace('反馈时请注明游戏名、BETA 0.1、', '反馈时请注明游戏名、BETA 0.1.1、')
    readme = readme.replace('内部构建：2026.09.10-r3（R2 + 回看按钮修复）。',
                            '内部构建：2026.09.14-r4（BETA 0.1 内容 + 字体缺字修复）。')
    (player / '使用说明.txt').write_text(readme, encoding='utf-8-sig', newline='\r\n')
    archive = output / 'MuvLuv_PF_CN_Patch_BETA_0.1.1.zip'
    ab.OUTPUT = player
    ab.build_deterministic_zip(player, archive)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist()) == {exe.name, '使用说明.txt'}
        assert digest(z.read(exe.name)) == ab.sha256(exe)
    sums = output / 'MuvLuv_PF_CN_Patch_BETA_0.1.1_SHA256SUMS.txt'
    sums.write_text(f'{ab.sha256(archive)}  {archive.name}\n', encoding='ascii')
    artifacts = dict(game='pf', version=manifest['version'], build_id=manifest['build_id'],
                     tag='pf-BETA-0.1.1', asset=archive.name, sha256=ab.sha256(archive),
                     bytes=archive.stat().st_size, exe_sha256=ab.sha256(exe),
                     font_sha256=NEW_FONT, runtime_sha256=NEW_DLL, added_characters=ADDED,
                     old_zip_sha256=OLD_ZIP, changed_package_members=changed,
                     normalized_rebuild_match=True, build=report)
    write_json(output / 'artifacts.json', artifacts)
    return artifacts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('old-zip', 'donor', 'output', 'csc'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_release(args.old_zip, args.donor, args.output, args.csc), indent=2))
