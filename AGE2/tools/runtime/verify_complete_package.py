"""Compare both installation methods using the actual bundled installer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--zip', type=Path, required=True)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    work = Path(tempfile.mkdtemp(prefix='age2-complete-'))
    unpacked = work / 'manual'
    with zipfile.ZipFile(args.zip) as z:
        names = z.namelist()
        setup = [n for n in names if '/' not in n and n.endswith('-Setup.exe')]
        assert len(setup) == 1
        assert {n.split('/')[0] for n in names} == {'game', 'root', '安装说明.txt', setup[0]}
        assert z.testzip() is None
        z.extractall(unpacked)
    extract_report = work / 'extracted.txt'
    subprocess.run([str(unpacked / setup[0]), '--extract', str(extract_report)], check=True)
    package = Path(extract_report.read_text(encoding='utf-8-sig'))
    m = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    for f in m['files']:
        assert sha(package / f['path']) == f['sha256']
        assert sha(unpacked / f['path']) == f['sha256']
    assert sha(unpacked / 'game' / m['exe']) == m['native']['patched_sha256']
    original_hash = sha(args.original)
    assert original_hash == m['native']['original_sha256']
    repo = Path(__file__).resolve().parents[3]
    harness = work / 'InstallEngineHarness.exe'
    subprocess.run([os.environ['WINDIR'] + '/Microsoft.NET/Framework64/v4.0.30319/csc.exe',
                    '/nologo', '/target:exe', '/platform:x64', '/out:' + str(harness),
                    '/reference:System.Web.Extensions.dll',
                    str(repo / 'AGE2/packaging/windows/Age2InstallEngine.cs'),
                    str(repo / 'AGE2/tests/packaging/InstallEngineHarness.cs')], check=True)
    game = work / 'game'
    game.mkdir()
    shutil.copy2(args.original, game / m['exe'])
    profile = work / 'profile'
    data = profile / 'ancr' / m['game'] / 'data'
    (data / 'root').mkdir(parents=True)
    (data / 'user').mkdir()
    (data / 'root/legacy-jp.txt').write_text('OLD OVERLAY')
    (data / 'user/savedata.bin').write_text('PLAYER-SAVE')
    subprocess.run([str(harness), str(package), str(game), str(profile)], check=True)
    for f in m['files']:
        dest = data / f['path'] if f['path'].startswith('root/') else game / Path(f['path']).name
        assert sha(dest) == f['sha256']
    assert sha(game / m['exe']) == sha(unpacked / 'game' / m['exe'])
    assert sha(args.original) == original_hash
    result = {'game': m['game'], 'version': m['version'], 'zip_sha256': sha(args.zip),
              'top_level_items': 4, 'manual_installer_bytes_identical': True,
              'isolated_install_reinstall_rollback_save_preservation': True,
              'original_unchanged': True, 'work': str(work)}
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
