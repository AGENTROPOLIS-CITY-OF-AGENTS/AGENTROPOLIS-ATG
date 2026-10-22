import assert from 'node:assert/strict';
import {validateScene,compilePreview} from './scene-core.mjs';
import {readFileSync} from 'node:fs';
const input = JSON.parse(readFileSync(new URL('./examples/builder-commons.json', import.meta.url)));
assert.equal(validateScene(input), true);
const first=compilePreview(input), second=compilePreview(input);
assert.deepEqual(first,second);
assert.equal(first.objects.length,2);
assert.equal(first.objects[0].vertices.length,8);
assert.equal(first.objects[0].faces.length,12);
for (const mutation of [
  s=>s.scene.objects[0].dimensions[0]=-1,
  s=>s.scene.objects[0].dimensions[0]=Infinity,
  s=>s.scene.objects.push({...s.scene.objects[0]}),
  s=>s.execution.mode='execute',
  s=>s.scene.objects[0].generator='eval',
]) {
 const s=structuredClone(input);mutation(s);assert.throws(()=>validateScene(s));
}
console.log('GEOMANCY scene-core tests passed');
