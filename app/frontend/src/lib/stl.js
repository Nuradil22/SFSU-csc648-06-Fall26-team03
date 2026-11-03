import { Group, Mesh, Matrix4 } from 'three';
import { STLExporter } from 'three/addons/exporters/STLExporter.js';

export function exportSceneSTL(scene) {
    scene.updateWorldMatrix(true, true);
    const meshes = new Group();
    scene.traverseVisible((object) => {
        if (!object.isMesh || !object.geometry?.getAttribute('position')) return;
        if (object.isSkinnedMesh || object.morphTargetInfluences?.some(Boolean)) {
            throw new Error('Animated or deformed meshes are not supported by this scan export.');
        }
        const position = object.geometry.getAttribute('position');
        const count = object.geometry.index?.count ?? position.count;
        if (!count || count % 3) throw new Error('The model contains invalid triangle geometry.');
        for (let i = 0; i < position.count; i++) {
            if (![position.getX(i), position.getY(i), position.getZ(i)].every(Number.isFinite)) {
                throw new Error('The model contains invalid vertex coordinates.');
            }
        }
        const addMesh = (matrix) => {
            const mesh = new Mesh(object.geometry);
            mesh.matrixAutoUpdate = false;
            mesh.matrix.copy(matrix);
            meshes.add(mesh);
        };
        if (object.isInstancedMesh) {
            for (let i = 0; i < object.count; i++) {
                const matrix = new Matrix4();
                object.getMatrixAt(i, matrix);
                addMesh(matrix.premultiply(object.matrixWorld));
            }
        } else {
            addMesh(object.matrixWorld);
        }
    });
    if (!meshes.children.length) throw new Error('No visible triangle meshes were found in this model.');
    meshes.updateMatrixWorld(true);
    return new STLExporter().parse(meshes, { binary: true });
}
