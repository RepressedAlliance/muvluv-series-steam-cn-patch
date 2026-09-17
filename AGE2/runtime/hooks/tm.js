// Extend the native whitelist {en=2,jp=0,terminator=12} with ck=9.
// Keep native fallback-to-English for unsupported automatic Windows locales.
patch(0x979c38,[2,0,0,0,0,0,0,0,9,0,0,0,12,0,0,0]);
// Keep game language ID 9 and activate the dormant ZH resource suffix.
// Stop at 0x55171: the native suffix table still jumps there for English.
patch(0x5515f,[0x89,0x8b,0x98,0,0,0,0xe9,0x1f,0,0,0],0x12);
patch(0x77086,[0x90,0x90]);
// ZH ImageAssets are registered by build_zh_gui.py, alongside original JA/EN labels.
// Stock image rebinding recognizes only a CURRENT _ja/_en suffix. Accept _zh too,
// so a Chinese image can subsequently switch back to either original language.
// Hook the six-byte comparison CALL, not its two-byte TEST: the earlier JE
// targets the instruction immediately after TEST/JNE and must remain intact.
const zhSuffix=Memory.allocUtf8String('zh');keep.push(zhSuffix);
for(const rva of [0x77699,0x77860,0x77a75,0x77c54]) {
  Interceptor.attach(p(rva),{onEnter(){
    if(this.context.rcx.readUtf8String(2)==='zh') {
      this.context.rdx=zhSuffix;events.guiZhRewrites++;
    }
  }});
}

// Four slider positions: Auto, English, Japanese, Chinese. Keep the saved preference
// separate from the effective locale so Auto remains selected after resolution.
patch(0xbc69c,[0x90,0x90,0x90]);
const selectorMap=Memory.alloc(16);[-1,2,0,9].forEach((v,i)=>selectorMap.add(i*4).writeS32(v));keep.push(selectorMap);
const selectorAddress=Memory.alloc(8);selectorAddress.writePointer(selectorMap);
patch(0xbc69f,[0x48,0xb8,...new Uint8Array(selectorAddress.readByteArray(8)),0x42,0x8b,0x0c,0x80],24);
patch(0xbc6cf,[0x90,0x90,0x90]);
Interceptor.attach(p(0xbafc5),{onEnter(){const preference=this.context.r15.add(0x70).readS32();const index=preference===-1?0:preference===2?1:preference===0?2:3;this.context.rdx=ptr(index);}});
// The ADV options state stored and compared every non-JP language as English.
// Retain the effective locale ID on both sides, allowing CN<->EN to redraw now.
patch(0x1248ed,[0x90,0x90,0x90]);
patch(0x124991,[0x90,0x90,0x90]);
// Native ADV and GUI text caches compare only the string/size. A speaker such
// as 山口提督 is identical in JP/CN, but its font must follow the selected locale.
// Invalidate each cache once per effective-language transition, retaining the
// ordinary unchanged-text fast path for all subsequent frames.
const advTextLocales=new Map(), guiTextLocales=new Map();
Interceptor.attach(p(0xc5fb2),{onEnter(){
  const key=this.context.rsi.toString(), current=language(), previous=advTextLocales.get(key);
  advTextLocales.set(key,current);
  if(previous!==undefined && previous!==current)this.context.rax=ptr(0);
}});
// Font/text refresh can change the final ADV height after its parent position
// was cached using the previous locale's metrics. Reuse native position dirty
// flags once when that height or locale changes, before native anchoring runs.
// Do not change line breaks, coordinates, or animation-owned pointers.
const advPositionMetrics=new Map();
Interceptor.attach(p(0xd4015),{onEnter(){
  const node=this.context.rsi, model=this.context.rdi;
  const key=node.toString()+':'+model.toString(), current=language();
  const height=this.context.rbp.sub(0x7c).readFloat();
  if(!Number.isFinite(height))return;
  const previous=advPositionMetrics.get(key);
  if(previous && previous.locale===current && Math.abs(previous.height-height)<0.01)return;
  if(!previous && advPositionMetrics.size>=2048)advPositionMetrics.delete(advPositionMetrics.keys().next().value);
  advPositionMetrics.set(key,{locale:current,height});
  if(current!==9 && previous?.locale!==9)return;
  model.add(0x54).writeU8(1);
  model.add(0x50).writeU32(0x01010101);
}});
Interceptor.attach(p(0x4bf883),{onEnter(){
  const key=this.context.rdi.toString(), current=language(), previous=guiTextLocales.get(key);
  guiTextLocales.set(key,current);
  if(previous!==undefined && previous!==current)this.context.r15=ptr(1);
}});
// ADV's localized-image resolver has a separate binary jp/en locale source.
// Give CN an explicit _ck cache key; JP and EN retain the native names.
Interceptor.attach(p(0x126090),{onLeave(ret){
  if(language()!==9)return;
  const capacity=ret.add(24).readU64();
  const data=capacity.compare(16)>=0?ret.readPointer():ret;
  data.writeUtf8String('ck');ret.add(16).writeU64(2);
}});
// Normal rendering can continue to use existing non-Japanese text index; getter below provides CN independently.

const core=Process.getModuleByName('erc_nospfx.dll');
const hash=new NativeFunction(core.getExportByName('eg4F9A1AD31941D4DC1A2A49D9F7A98EB8'),'uint',['pointer','uint']);
const findField=new NativeFunction(core.getExportByName('egA1C937BE423056E67BE4F660B86F6920'),'pointer',['pointer','pointer']);
const getValue=new NativeFunction(core.getExportByName('egB29267A4B92B33BB80DCCACC68D153DA'),'pointer',['pointer','uint']);
const getVariant=new NativeFunction(core.getExportByName('eg8D695114B7D01F77825EFD948094E590'),'pointer',['pointer','pointer']);
const cnName=Memory.allocUtf8String('zh_hans'), cnField=Memory.alloc(16);
cnField.writePointer(cnName);cnField.add(8).writeU32(hash(cnName,7));keep.push(cnName,cnField);
log('cn-hash',cnField.add(8).readU32().toString(16));
Interceptor.attach(p(0x5ec34), {onEnter() {
  try {
    const record=this.context.rbp.add(8).readPointer();
    const node=this.context.rsi.sub(0x30);
    cnCache.delete(node.toString());
    const field=findField(record,cnField);
    if(field.isNull())return;
    const value=getValue(field,0);
    if(value.isNull())return;
    const variant=Memory.alloc(32);getVariant(value,variant);
    if(variant.add(16).readU8()===6) {
      const text=variant.readPointer();
      if(!text.isNull()) {
        // Own the CN string independently of the loader's temporary variant.
        cnCache.set(node.toString(),Memory.allocUtf8String(text.readUtf8String()));events.cnLoaded++;
      }
    }
  } catch(e) { log('cn-load-error',String(e)); }
}});
// Both normal messages and the alternate history builder enumerate JP/EN.
// Extend their private iteration range without touching adjacent native data.
const historyLanguages=Memory.alloc(Process.pageSize,{near:p(0x9923a),maxDistance:0x7fffffff});
[0,2,9].forEach((value,i)=>historyLanguages.add(4*i).writeS32(value));keep.push(historyLanguages);
for(const [site,target] of [[0x9923a,historyLanguages],[0xaec59,historyLanguages],
 [0x99241,historyLanguages.add(12)],[0x99333,historyLanguages.add(12)],[0xaf3d3,historyLanguages.add(12)]]) {
 const delta=target.sub(p(site+7)).toInt32();
 if(!p(site+7).add(delta).equals(target))throw new Error('Backlog language table out of range');
 Memory.patchCode(p(site+3),4,code=>code.writeS32(delta));
}
// Preserve the explicit language requested by the history builder. The native
// wrapper otherwise reduces every non-Japanese language to the English index.
const explicitTextLanguages=new Map();
Interceptor.attach(p(0x5e480),{onEnter(args){
 this.thread=Process.getCurrentThreadId();this.previous=explicitTextLanguages.get(this.thread);
 explicitTextLanguages.set(this.thread,args[3].toInt32());
},onLeave(){
 if(this.previous===undefined)explicitTextLanguages.delete(this.thread);
 else explicitTextLanguages.set(this.thread,this.previous);
}});
function requestedTextLanguage(){
 const explicit=explicitTextLanguages.get(Process.getCurrentThreadId());
 return explicit===undefined?language():explicit;
}
Interceptor.attach(p(0x5ef20),{onEnter(args){
 const requested=requestedTextLanguage();
 if(explicitTextLanguages.has(Process.getCurrentThreadId())||requested===9)args[3]=ptr(requested===0?0:1);
}});
Interceptor.attach(p(0x5f0e2), {onEnter() {
  if(requestedTextLanguage()!==9)return;
  const value=cnCache.get(this.context.rbx.toString());
  if(value) {this.context.rax=value;events.cnRead++; if(events.cnRead<12)log('cn-text',value.readUtf8String().slice(0,120));}
  else log('cn-cache-missing',this.context.rbx.toString());
}});
Interceptor.attach(p(0x1e0860),{onEnter(args){log('language-selection',args[0].toInt32());},onLeave(){events.lang.push(language());}});


// CN typography: use the original CJK node size, not FontSizeUS/EN.
// Run after native locale selection and before rasterization/measurement.
// The original size is retained by the engine separately from the active size.
Interceptor.attach(p(0x4bf82b),{onEnter(){
 if(language()===9){const node=this.context.rsi;node.add(0x1cf).writeU8(node.add(0x1d0).readU8());}
}});
