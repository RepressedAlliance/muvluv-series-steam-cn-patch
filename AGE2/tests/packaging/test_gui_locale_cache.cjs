const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../runtime/hooks/tda_gui_locale.js'),'utf8');
for (const sequence of [[9,0,9,2,9],[0,9,0,2,9]]) {
  let locale=sequence[0], callback;
  vm.runInNewContext(source,{Map,language:()=>locale,p:x=>x,ptr:x=>x,
    Interceptor:{attach:(address,hook)=>{assert.equal(address,0x20739e);callback=hook.onEnter;}}});
  const invoke=(node,dirty=0)=>{const context={rdi:node,r9:dirty};callback.call({context});return context.r9;};
  assert.equal(invoke('same-label'),0);
  for (const next of sequence.slice(1)) {
    locale=next;
    assert.equal(invoke('same-label'),1,'language change must redraw identical text');
    assert.equal(invoke('same-label'),0,'unchanged frames must retain cache');
    assert.notEqual(invoke('changed-label',7),0,'native dirty state must remain true');
  }
}
console.log('GUI locale cache: both startup directions, English, unchanged-frame path passed');
