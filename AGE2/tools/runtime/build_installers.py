"""Build the five self-contained Windows installers from reviewed staging."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,zipfile

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--staging',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--game',choices=['tm','tda00','tda01','tda02','tda03'],action='append')
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[2]/'packaging/windows'
    compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file():raise FileNotFoundError(compiler)
    args.output.mkdir(parents=True,exist_ok=False)
    report={}
    for game in args.game or ['tm','tda00','tda01','tda02','tda03']:
        package=args.staging/game
        manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8'))
        if manifest['game']!=game:raise ValueError('Wrong game package')
        payload=args.output/(game+'-payload.zip')
        with zipfile.ZipFile(payload,'x',zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
            for name in ('manifest.json','exe.delta.json'):
                archive.write(package/name,name)
            for entry in manifest['files']:
                path=package/entry['path'];data=path.read_bytes()
                if len(data)!=entry['size'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
                    raise ValueError('Changed staged file: '+str(path))
                archive.writestr(entry['path'],data)
        output=args.output/(game+'-CN-'+manifest['version']+'-review.exe')
        command=[str(compiler),'/nologo','/target:winexe','/platform:x64',
                 '/out:'+str(output.resolve()),'/resource:'+str(payload.resolve())+',payload.zip',
                 '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll',
                 '/reference:System.Web.Extensions.dll','/reference:System.IO.Compression.dll',
                 '/reference:System.IO.Compression.FileSystem.dll',
                 str(source/'Age2Installer.cs'),str(source/'Age2InstallEngine.cs')]
        subprocess.run(command,check=True)
        report[game]={'installer':str(output.resolve()),'bytes':output.stat().st_size,
                      'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'status':'review-candidate'}
        print(json.dumps(report[game]),flush=True)
    (args.output/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
