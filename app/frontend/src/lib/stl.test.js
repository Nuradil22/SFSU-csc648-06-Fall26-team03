import test from 'node:test';
import assert from 'node:assert/strict';
import { BoxGeometry, Group, Mesh, BoxHelper, InstancedMesh, Matrix4 } from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { exportSceneSTL } from './stl.js';

test('binary STL preserves nested transforms and multiple meshes, excludes helpers and hidden meshes', () => {
    const root = new Group();
    root.position.x = 10;
    const nested = new Group();
    nested.scale.setScalar(2);
    root.add(nested);
    nested.add(new Mesh(new BoxGeometry(1, 1, 1)));
    const second = new Mesh(new BoxGeometry(1, 1, 1));
    second.position.x = 4;
    root.add(second);
    root.add(new BoxHelper(second));
    const hidden = new Mesh(new BoxGeometry(100, 100, 100));
    hidden.visible = false;
    root.add(hidden);
    const data = exportSceneSTL(root);
    assert.equal(data.getUint32(80, true), 24);
    assert.equal(data.byteLength, 84 + 24 * 50);
    const geometry = new STLLoader().parse(data.buffer);
    geometry.computeBoundingBox();
    assert.equal(geometry.boundingBox.min.x, 9);
    assert.equal(geometry.boundingBox.max.x, 14.5);
    assert.equal(geometry.boundingBox.min.y, -1);
});

test('exports each instance with its transform', () => {
    const mesh = new InstancedMesh(new BoxGeometry(), undefined, 2);
    mesh.setMatrixAt(1, new Matrix4().makeTranslation(5, 0, 0));
    const data = exportSceneSTL(mesh);
    assert.equal(data.getUint32(80, true), 24);
    const geometry = new STLLoader().parse(data.buffer);
    geometry.computeBoundingBox();
    assert.equal(geometry.boundingBox.max.x, 5.5);
});

test('rejects empty scenes and non-finite geometry', () => {
    assert.throws(() => exportSceneSTL(new Group()), /No visible triangle/);
    const mesh = new Mesh(new BoxGeometry());
    mesh.geometry.attributes.position.setX(0, NaN);
    assert.throws(() => exportSceneSTL(mesh), /invalid vertex/);
});
