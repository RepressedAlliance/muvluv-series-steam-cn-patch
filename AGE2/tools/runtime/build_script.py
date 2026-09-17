"""Assemble a local-only runtime from the version-specific native hooks."""
from pathlib import Path
import json

HEADER=r'''
'use strict';
const exe=Process.mainModule, base=exe.base, p=r=>base.add(r);
const keep=[], cnCache=new Map();
// Patched machine code holds raw addresses that the JS garbage collector
// cannot trace. Keep these allocations alive after the initialization block.
globalThis.age2RuntimeAllocations=keep;
const events={cnLoaded:0,cnRead:0,guiZhRewrites:0,lang:[]};
const language=()=>p(CONFIG.language_rva).readS32();
function log(kind,value) {}
function patch(rva,bytes,size=bytes.length) {
  Memory.patchCode(p(rva),size,code=>code.writeByteArray(bytes.concat(Array(Math.max(0,size-bytes.length)).fill(0x90))));
}
function branch(from,to,size) {
  Memory.patchCode(p(from),size,code=>{
    const writer=new X86Writer(code,{pc:p(from)});writer.putJmpAddress(p(to));
    while(writer.offset<size)writer.putNop();writer.flush();
  });
}
// All ordinary resources are physical loose files under data/root. Only the
// Chinese font configuration needs conditional selection; JP/EN keep their
// original configuration and original font files.
const nt=Process.getModuleByName('ntdll.dll');
for(const [name,arg] of [['NtCreateFile',2],['NtOpenFile',2],['NtQueryAttributesFile',0],['NtQueryFullAttributesFile',0]]) {
  Interceptor.attach(nt.getExportByName(name),{onEnter(args){
    if(language()!==9)return;
    const oa=args[arg];if(oa.isNull())return;
    const us=oa.add(16).readPointer();if(us.isNull())return;
    const path=us.add(8).readPointer().readUtf16String(us.readU16()/2);
    if(!path || !/[\\/]assets[\\/]data[\\/]gui[\\/]font[\\/]font(?:_(?:en|zh|ck|zh_hans))?\.cfg$/i.test(path))return;
    const dest=path.replace(/font(?:_(?:en|zh|ck|zh_hans))?\.cfg$/i,'Font_cn.cfg');
    const buf=Memory.allocUtf16String(dest),nu=Memory.alloc(16),no=Memory.alloc(48);
    Memory.copy(no,oa,48);nu.writeU16(dest.length*2);nu.add(2).writeU16(dest.length*2+2);nu.add(8).writePointer(buf);
    no.add(16).writePointer(nu);this.refs=[buf,nu,no];args[arg]=no;
  }});
}
'''


def build_script(game: str, ready_rva: int, hooks: Path) -> str:
    if game not in ('tm','tda00','tda01','tda02','tda03'):
        raise ValueError('Unknown AGE2 game')
    body=(hooks/(game+'.js')).read_text(encoding='utf-8')
    body+='\n'+(hooks/'save_preview.js').read_text(encoding='utf-8')
    if game.startswith('tda'):
        body+='\n'+(hooks/'tda_gui_locale.js').read_text(encoding='utf-8')
    # Optional generated, version-specific body layout. Log behavior remains
    # in the existing game hook and is not changed by this module.
    layout=hooks/'body_layout'/(game+'.js')
    if layout.exists():
        body+='\n'+layout.read_text(encoding='utf-8')
    # Release code must never inherit the research profile, Steam isolation,
    # console attachment, or externally callable language mutation helpers.
    forbidden=('SteamInternal_FindOrCreateUserInterface','steam-isolation','no_load_from_cloud',
               'cfg.profile','cfg.cn','rpc.exports','fontDiagnostics')
    if any(value in body for value in forbidden):
        raise ValueError('Research-only behavior remains in release hook')
    config={'game':game,'language_rva':0xb03a18 if game=='tm' else 0xa58f5c}
    init='const CONFIG='+json.dumps(config)+';\n'
    init+='try {\n'+HEADER+body+'\nInterceptor.flush();p('+str(ready_rva)+').writeU8(1);\n'
    init+='} catch (error) {\n'
    init+='const kernel=Process.getModuleByName("kernel32.dll");\n'
    init+='new NativeFunction(kernel.getExportByName("OutputDebugStringW"),"void",["pointer"])(Memory.allocUtf16String("AGE2 Chinese runtime: "+String(error)));\n}\n'
    return init
