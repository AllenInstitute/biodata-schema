const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../docs/source/_static/coordinate_system_builder.html'), 'utf8');
test('literal control selectors exist in the builder', () => {
  const ids = new Set(Array.from(source.matchAll(/\bid="([^"]+)"/g), match => match[1]));
  for (const match of source.matchAll(/getElementById\('([^']+)'\)/g)) {
    assert.ok(ids.has(match[1]), `Missing control ${match[1]}`);
  }
});

const functions = ['getDeviceNormal', 'getDeviceBasis', 'inferHandedness', 'inferDevHandedness', 'vecToDir', 'buildExport', '_axisAngleRotate', 'applyRotation', 'applyBasisTranslation', 'applyTransformToState'];
const exportControl = { value: '' };
const context = vm.createContext({
  state: {
    device: { type: 'probe', longDir: 'DU', widDir: 'AP', csName: 'Device', csOrigin: 'TIP', csUnit: 'mm' },
    cs: { name: 'BREGMA_RAS', origin: 'BREGMA', unit: 'mm', axes: [
      { name: 'ML', direction: 'LR' }, { name: 'AP', direction: 'PA' }, { name: 'SI', direction: 'IS' },
    ] },
    transforms: [],
  },
  isFullMode: true,
  document: { getElementById: () => exportControl },
});
vm.runInContext(source.match(/^const DIR_TO_THREEJS = \{[^]*?^};/m)[0], context);
for (const name of functions) {
  const match = source.match(new RegExp(`^function ${name}\\([^]*?^}`, 'm'));
  assert.ok(match, `Missing builder function ${name}`);
  vm.runInContext(match[0], context);
}

function close(actual, expected) {
  actual.forEach((value, index) => assert.ok(Math.abs(value - expected[index]) < 1e-10, `${actual} != ${expected}`));
}

for (const type of ['probe', 'monitor']) {
  test(`${type} export directions and handedness match the preview`, () => {
    context.state.device.type = type;
    context.state.device.longDir = type === 'probe' ? 'DU' : 'PA';
    context.state.device.widDir = type === 'probe' ? 'AP' : 'LR';
    context.buildExport();
    const deviceCode = exportControl.value.split('device_cs =')[1].split('transform =')[0];
    const directions = Array.from(deviceCode.matchAll(/direction=Direction\.(\w+)/g), match => match[1]);
    assert.deepEqual(directions, type === 'probe' ? ['AP', 'IS', 'LR'] : ['LR', 'IS', 'PA']);
    assert.match(deviceCode, /handedness=Handedness.LEFT/);
    assert.equal(context.inferDevHandedness(), 'left');
  });

  for (const axis of [0, 1, 2]) {
    test(`${type} local axis ${axis} matches the exported basis`, () => {
      context.state.device.type = type;
      const width = [1, 0, 0];
      const direction = [0, 0, 1];
      const basis = context.getDeviceBasis(width, direction);
      const translation = [0, 0, 0];
      translation[axis] = 2;
      const result = context.applyTransformToState([0, 0, 0], direction, width, {
        type: 'T', frame: 'local', translation,
      }, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
      close(result.pos, basis[axis].map(value => value * 2));
      const angles = [0, 0, 0];
      angles[axis] = 90;
      const rotated = context.applyTransformToState([1, 2, 3], direction, width, {
        type: 'R', referenceCoordinateSystem: 'local', pivot: 'local', angles,
      }, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
      close(rotated.pos, [1, 2, 3]);
      close(rotated.dir, context._axisAngleRotate(direction, basis[axis], Math.PI / 2));
      close(rotated.wid, context._axisAngleRotate(width, basis[axis], Math.PI / 2));
      const moved = context.applyTransformToState(rotated.pos, rotated.dir, rotated.wid, {
        type: 'T', frame: 'local', translation,
      }, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
      close(moved.pos, context.getDeviceBasis(rotated.wid, rotated.dir)[axis].map((value, index) => [1, 2, 3][index] + value * 2));
    });
  }
}