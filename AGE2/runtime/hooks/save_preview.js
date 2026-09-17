// Save thumbnails carry their own localized synopsis, separate from the log.
// Ask the original synopsis builder to store CN alongside JP and EN.
// Leave serialization, slot selection and native string ownership unchanged.
const savePreviewLanguages=Memory.alloc(12);
[0,2,9].forEach((v,i)=>savePreviewLanguages.add(i*4).writeS32(v));
keep.push(savePreviewLanguages);
// The native suffix writer conflates traditional/simplified Chinese as "zh".
// The save reader parses "zh" as 8 and "ck" as 9. Scope the correction to
// synopsis serialization so image resource suffix behavior is untouched.
const savePreviewCnKey=Memory.allocUtf8String('ck');
keep.push(savePreviewCnKey);
const saveKeySite=CONFIG.game==='tm'?0x150c61:CONFIG.game==='tda03'?0x3c91ef:0x3c918f;
Interceptor.attach(p(saveKeySite),{onEnter(){
  if(this.context.rbx.add(0x20).readS32()===9)this.context.rax=savePreviewCnKey;
}});
if(CONFIG.game==='tm') {
  Interceptor.attach(p(0x152c5d),{onEnter(){
    this.context.rbx=savePreviewLanguages;
    this.context.rdi=savePreviewLanguages.add(12);
  }});
} else {
  const savePreviewVector=Memory.alloc(24);
  savePreviewVector.writePointer(savePreviewLanguages);
  savePreviewVector.add(8).writePointer(savePreviewLanguages.add(12));
  savePreviewVector.add(16).writePointer(savePreviewLanguages.add(12));
  keep.push(savePreviewVector);
  Interceptor.attach(p(CONFIG.game==='tda03'?0x2b78b0:0x2b7690),{
    onLeave(ret){ret.replace(savePreviewVector);}
  });
}
