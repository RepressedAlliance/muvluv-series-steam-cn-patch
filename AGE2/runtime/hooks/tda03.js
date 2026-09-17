// TDA00's own whitelist terminates at 11, unlike TM's 12.
patch(0x8b4090,[2,0,0,0,0,0,0,0,9,0,0,0,11,0,0,0]);
const choiceMap=Memory.alloc(16); [-1,2,0,9].forEach((v,i)=>choiceMap.add(i*4).writeS32(v));keep.push(choiceMap);
Memory.patchCode(p(0x2a6f84),23,code=>{
 const w=new X86Writer(code,{pc:p(0x2a6f84)});
 w.putMovRegAddress('rax',choiceMap); w.putBytes([0x8b,0x1c,0x98]);
 while(w.offset<23)w.putNop(); w.flush();
});
const preference=new NativeFunction(p(0x4f6b0),'int',[]);
Interceptor.attach(p(0x2a766d),{onEnter(){
 const value=preference();this.context.rdi=ptr(value===-1?0:value===2?1:value===0?2:3);
}});
// TDA loads jp/en/zh_hant/zh_hans and six other fields itself. No external cache.
// Backlog construction iterates a separate fixed {JP, EN} array. Point both
// boundaries at a three-language array without changing the loop instructions.
const historyLanguages=Memory.alloc(Process.pageSize,{near:p(0x2c26bc),maxDistance:0x7fffffff});
[0,2,9].forEach((value,i)=>historyLanguages.add(4*i).writeS32(value));keep.push(historyLanguages);
for(const [site,target] of [[0x2c26bc,historyLanguages],[0x2c2a4b,historyLanguages.add(12)]]) {
 const delta=target.sub(p(site+7)).toInt32();
 if(!p(site+7).add(delta).equals(target))throw new Error('Backlog language table out of range');
 Memory.patchCode(p(site+3),4,code=>code.writeS32(delta));
}
// Explicit JP/EN history requests must not be replaced with the current CN
// display language. Keep all three strings available when the player switches.
const explicitTextLanguages=new Map();
Interceptor.attach(p(0x2b5fd0),{onEnter(args){
 this.thread=Process.getCurrentThreadId();this.previous=explicitTextLanguages.get(this.thread);
 explicitTextLanguages.set(this.thread,args[3].toInt32());
},onLeave(){
 if(this.previous===undefined)explicitTextLanguages.delete(this.thread);
 else explicitTextLanguages.set(this.thread,this.previous);
}});
Interceptor.attach(p(0x2b5dc0),{onEnter(args){
 const explicit=explicitTextLanguages.get(Process.getCurrentThreadId());
 this.cn=(explicit===undefined?language():explicit)===9;
 if(explicit!==undefined)args[3]=ptr(explicit===0?0:explicit===9?3:1);
 if(this.cn){args[3]=ptr(3);this.id=args[1].readUtf8String();}
},onLeave(ret){if(this.cn){events.cnRead++;if(events.cnRead<30)log('cn-text',{id:this.id,text:ret.readUtf8String()});}}});
Interceptor.attach(p(0x2b7650),{onLeave(ret){if(language()===9)ret.replace(9);}});
// Native GUI rebinding recognizes only _ja/_en. Recognize _zh at these
// suffix comparisons as well, so leaving Chinese restores the target assets.
const zhSuffix=Memory.allocUtf8String('zh');keep.push(zhSuffix);
for(const site of [0x2b6ca4,0x2b6cf2,0x2b6e74,0x2b6ec2,0x2b7067,0x2b722b,0x2b75e9]){
 Interceptor.attach(p(site),{onEnter(){
  if(this.context.rcx.readUtf8String(2)==='zh')this.context.rdx=zhSuffix;
 }});
}
Interceptor.attach(p(0x3039e0),{onLeave(ret){
 if(language()!==9)return;
 const capacity=ret.add(24).readU64();
 const data=capacity.compare(16)>=0?ret.readPointer():ret;
 data.writeUtf8String('ck');ret.add(16).writeU64(2);
}});
Interceptor.attach(p(0x51950),{onEnter(args){log('language-selection',args[0].toInt32());},onLeave(){events.lang.push(language());}});

// CN typography: use the original CJK node size, not FontSizeUS/EN.
// Run after native locale selection and before rasterization/measurement.
// The original size is retained by the engine separately from the active size.
Interceptor.attach(p(0x20734a),{onEnter(){
 if(language()===9){const node=this.context.rsi;node.add(0x1ab).writeU8(node.add(0x1ac).readU8());}
}});
