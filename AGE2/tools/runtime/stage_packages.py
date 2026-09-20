"""Collect explicit runtime resources into new, reviewable per-game packages."""
import argparse,datetime,hashlib,json,shutil,sys
from pathlib import Path
import xml.etree.ElementTree as ET
repo=Path(__file__).resolve().parents[3]
bootstrap=argparse.ArgumentParser(add_help=False);bootstrap.add_argument('--workspace',type=Path,required=True)
workspace_args,_=bootstrap.parse_known_args();O=workspace_args.workspace.resolve();A=O/'five-game-review'
sys.path[:0]=[str(repo),str(O/'build-deps')]
from AGE2.tools.runtime.pe_loader import embed_runtime
from AGE2.tools.runtime.exe_delta import make_delta
from AGE2.tools.runtime.build_script import build_script

parser=argparse.ArgumentParser(parents=[bootstrap]);parser.add_argument('--game',choices=['tm','tda00','tda01','tda02','tda03'],action='append');parser.add_argument('--versions',type=Path)
args=parser.parse_args();games=args.game or ['tm','tda00','tda01','tda02','tda03']
versions=json.loads(args.versions.read_text(encoding='utf-8')) if args.versions else {}
build=A/'package-staging'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');build.mkdir(parents=True,exist_ok=False)
summary={}
for game in games:
    runtime=A/(game+'-runtime');cfg=json.loads((runtime/'config.json').read_text(encoding='utf-8'))
    package=build/game;root=package/'root';root.mkdir(parents=True)
    sources={}
    def copy(source,relative):
        relative=Path(relative);target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target);sources[relative.as_posix()]=str(source)
    # The three native boot files and required four-choice GUI layouts/strings.
    native_profile=Path(cfg['data'])/'root'
    for rel in ('readme.txt','resident.list','data/hiscore.conf'):copy(native_profile/rel,rel)
    for source in native_profile.rglob('*'):
        if not source.is_file():continue
        relative=source.relative_to(native_profile)
        if source.suffix.lower()=='.gut' or source.name.lower()=='uistring.epk':copy(source,relative)
    # Include the working Chinese image banks, then prefer the latest reviewed
    # candidate for every matching name. No original JA/EN image is installed.
    for folder in (Path(cfg['cn']),A/'candidate'/game/'root'):
        for source in folder.rglob('*'):
            if not source.is_file():continue
            rel=source.relative_to(folder);suffix=source.suffix.lower()
            if suffix in ('.webp','.avif'):
                if source.stem.lower().endswith(('_ck','_zh')):copy(source,rel)
            elif suffix in ('.egpack','.otf','.ttf') or source.name.endswith('-OFL.txt') or source.name in ('BWCKKT-source.txt','MEBheiheiti-source.txt'):
                copy(source,rel)
            elif suffix=='.xml' and ('/staffroll/' in '/'+rel.as_posix() or folder==A/'candidate'/game/'root'):
                copy(source,rel)
    fontdir=Path('assets/data/gui/font')
    chinese=A/'candidate'/game/'root'/fontdir/'Font.cfg'
    if not chinese.exists():chinese=chinese.with_name('font.cfg')
    copy(chinese,fontdir/'Font_cn.cfg')
    # The native faces remain primary. Add an open-source fallback for Chinese
    # save summaries when viewing the save list in Japanese or English.
    for name in ('Font.cfg','Font_en.cfg'):
        source=O/'refresh'/game/'original'/fontdir/name
        tree=ET.parse(source);params=tree.getroot().find('FontParamList')
        if any(p.findtext('Label')=='sub' for p in params):raise ValueError('Unexpected existing fallback')
        param=ET.SubElement(params,'FontParam')
        for key,value in [('Label','sub'),('FamilyName','sub'),('Bold','false'),('File','NotoSansSC-500.ttf')]:
            ET.SubElement(param,key).text=value
        target=root/fontdir/name;tree.write(target,encoding='utf-8',xml_declaration=True)
        sources[(fontdir/name).as_posix()]=str(source)+' + Chinese fallback'
    executable=Path(cfg['game'])/(game+'-win64vc14-release.exe')
    original=executable.read_bytes()
    if hashlib.sha256(original).hexdigest()!=cfg.get('expected_sha256','a8b4338129f416025e7de219f32dc60807b41d8a2f21d3145dfb2a3872416e46').lower():
        raise ValueError('Unexpected original executable')
    patched,report=embed_runtime(original)
    runtime_files=package/'game';runtime_files.mkdir()
    shutil.copy2(O/'runtime-deps/FridaGadget.dll',runtime_files/'FridaGadget.dll')
    shutil.copy2(O/'runtime-deps/COPYING-frida.txt',runtime_files/'COPYING-frida.txt')
    (runtime_files/'FridaGadget.config').write_text(json.dumps({'interaction':{'type':'script','path':'age2-cn.js','on_change':'ignore'},'runtime':'qjs'}),encoding='utf-8')
    script=build_script(game,report['ready_rva'],repo/'AGE2/runtime/hooks')
    (runtime_files/'age2-cn.js').write_text(script,encoding='utf-8')
    (package/'exe.delta.json').write_text(json.dumps(make_delta(original,patched),separators=(',',':')),encoding='utf-8')
    # Keep the patched native EXE outside the distribution for local testing.
    testdir=build/'test-executables';testdir.mkdir(exist_ok=True)
    (testdir/executable.name).write_bytes(patched)
    entries=[]
    for folder in ('root','game'):
        for path in sorted((package/folder).rglob('*')):
            if path.is_file():entries.append({'path':path.relative_to(package).as_posix(),'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'format':'age2-cn-package-1','status':'BETA' if versions else 'candidate','version':versions.get(game,{}).get('version','2026.09.15'),'game':game,
              'title':'帝都燃烧' if game=='tm' else 'Muv-Luv UNLIMITED '+game.upper(),
              'exe':executable.name,'native':report,'files':entries,
              'foundation':['readme.txt','resident.list','data/hiscore.conf']}
    (package/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (build/(game+'-sources.json')).write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
    summary[game]={'files':len(entries),'bytes':sum(e['size'] for e in entries),'egpack':sum(p.suffix.lower()=='.egpack' for p in root.rglob('*')),'package':str(package)}
    print(game,summary[game],flush=True)
(build/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(A/'latest-package-staging.json').write_text(json.dumps({'build':str(build),'games':summary},ensure_ascii=False,indent=2),encoding='utf-8')
