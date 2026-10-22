// Experimental GEOMANCY scene core. Not canonical ATG IR or an authority engine.
const finitePositive = n => typeof n === 'number' && Number.isFinite(n) && n > 0;
const assert = (ok, message) => { if (!ok) throw new Error(message); };
export function validateScene(input) {
  assert(input && typeof input === 'object' && !Array.isArray(input), 'scene object required');
  assert(input.profile === 'ATG:GEOMANCY' && input.profile_version === '0.1.0', 'unsupported profile');
  const s = input.scene;
  assert(s && typeof s === 'object', 'scene required');
  assert(typeof s.id === 'string' && /^[a-z0-9-]{1,64}$/.test(s.id), 'invalid scene id');
  assert(Number.isSafeInteger(s.seed) && s.seed >= 0 && s.seed <= 4294967295, 'invalid seed');
  assert(s.units === 'm' && s.coordinate_system === 'right-handed-y-up', 'unsupported spatial frame');
  assert(Array.isArray(s.objects) && s.objects.length <= 128, 'object limit exceeded');
  const ids = new Set();
  for (const o of s.objects) {
    assert(o && typeof o.id === 'string' && /^[a-z0-9-]{1,64}$/.test(o.id) && !ids.has(o.id), 'invalid or duplicate object id');
    ids.add(o.id);
    assert(o.generator === 'parametric-box', 'unsupported generator');
    assert(Array.isArray(o.dimensions) && o.dimensions.length === 3 && o.dimensions.every(n => finitePositive(n) && n <= 1000), 'invalid dimensions');
    assert(!o.material || (typeof o.material.base_color === 'string' && /^#[0-9a-fA-F]{6}$/.test(o.material.base_color)), 'invalid material');
  }
  assert(input.execution?.mode === 'preview-only' && input.execution?.authority_ref == null, 'preview-only boundary required');
  return true;
}
export function compilePreview(input) {
  validateScene(input);
  // Pure scene geometry: no network, eval, filesystem, credentials or agent actions.
  const objects = input.scene.objects.map(o => {
    const [x,y,z] = o.dimensions;
    return {id:o.id, type:'box', size:[x,y,z], vertices:[
      [-x/2,-y/2,-z/2],[x/2,-y/2,-z/2],[x/2,y/2,-z/2],[-x/2,y/2,-z/2],
      [-x/2,-y/2,z/2],[x/2,-y/2,z/2],[x/2,y/2,z/2],[-x/2,y/2,z/2]
    ], faces:[[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]],
    material:o.material?.base_color ?? '#12141A'};
  });
  return {scene_id:input.scene.id, seed:input.scene.seed, coordinate_system:input.scene.coordinate_system, units:'m', objects};
}
