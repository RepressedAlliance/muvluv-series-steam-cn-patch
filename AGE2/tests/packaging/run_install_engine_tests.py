"""Create isolated fixtures and exercise the actual Windows install engine."""
from pathlib import Path
import hashlib,json,subprocess,sys,uuid,os

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from AGE2.tools.runtime.exe_delta import make_delta

def main():
    # A new task-owned directory, with no connection to real Steam/AppData.
    work=ROOT/'local-internal'/'age2-installer-tests'/uuid.uuid4().hex[:8]
    package=work/'package';game=work/'game';profile=work/'profile'
    game.mkdir(parents=True,exist_ok=False)
    compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    harness=work/'InstallEngineHarness.exe'
    subprocess.run([str(compiler),'/nologo','/target:exe','/platform:x64',
                    '/out:'+str(harness.resolve()),'/reference:System.Web.Extensions.dll',
                    str(ROOT/'AGE2/packaging/windows/Age2InstallEngine.cs'),
                    str(ROOT/'AGE2/tests/packaging/InstallEngineHarness.cs')],check=True)
    original=b'MZ'+bytes(range(256))*64
    patched=original[:1024]+b'CN-HOOK'+original[1031:]+b'IMPORT-SECTION'
    exe='tm-win64vc14-release.exe';(game/exe).write_bytes(original)
    entries=[]
    foundation=['readme.txt','resident.list','data/hiscore.conf']
    files={**{'root/'+name:b'NATIVE-FOUNDATION-'+name.encode() for name in foundation},
           **{'game/'+name:b'RUNTIME-'+name.encode() for name in ['FridaGadget.dll','FridaGadget.config','COPYING-frida.txt','age2-cn.js']},
           'root/assets/story.egpack':'中文独立槽'.encode()}
    for relative,data in files.items():
        path=package/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        entries.append({'path':relative,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    delta=make_delta(original,patched)
    manifest={'format':'age2-cn-package-1','game':'tm','title':'Installer test fixture','version':'test','exe':exe,
              'native':{key:delta[key] for key in ['original_sha256','patched_sha256']},'files':entries,'foundation':foundation}
    (package/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    (package/'exe.delta.json').write_text(json.dumps(delta),encoding='utf-8')
    data=profile/'ancr/tm/data';(data/'root').mkdir(parents=True);(data/'user').mkdir()
    (data/'root/legacy-jp.txt').write_text('OLD-CHINESE-ON-JP',encoding='utf-8')
    (data/'user/savedata.bin').write_text('PLAYER-SAVE',encoding='utf-8')
    result=subprocess.run([str(harness),str(package),str(game),str(profile)],capture_output=True)
    (work/'stdout.bin').write_bytes(result.stdout);(work/'stderr.bin').write_bytes(result.stderr)
    report={'exit_code':result.returncode,'fixture':str(work)}
    (work/'result.json').write_text(json.dumps(report),encoding='utf-8')
    print(json.dumps(report));print(result.stdout.decode('utf-8',errors='replace'));print(result.stderr.decode('utf-8',errors='replace'))
    return result.returncode

if __name__=='__main__':raise SystemExit(main())
