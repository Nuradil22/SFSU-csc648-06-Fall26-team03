import { Component, Suspense, useEffect, useState } from "react";
import { exportSceneSTL } from "../../lib/stl";
import { Box3, Sphere } from "three";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";

import "./ModelViewer.css";

// Fraction of the viewer the model should fill on first load
const FIT_FILL = 0.7;

function Model({ url, onLoaded }) {
    const { scene } = useGLTF(url);
    const get = useThree((state) => state.get);
    const size = useThree((state) => state.size);

    useEffect(() => {
        onLoaded(scene);
        return () => onLoaded(null);
    }, [scene, onLoaded]);

    useEffect(() => {
        const { camera, controls } = get();
        // Bounding sphere of the whole scan — radius-based fitting handles
        // irregular geometry better than fitting each axis separately.
        const box = new Box3().setFromObject(scene);
        const sphere = box.getBoundingSphere(new Sphere());
        if (!Number.isFinite(sphere.radius) || sphere.radius === 0) return;

        // Distance at which the sphere fills FIT_FILL of the view, checking
        // both vertical and horizontal FOV so nothing clips on narrow screens.
        const verticalFov = (camera.fov * Math.PI) / 180;
        const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * (size.width / size.height));
        const smallestFov = Math.min(verticalFov, horizontalFov);
        const distance = sphere.radius / Math.sin(smallestFov / 2) / FIT_FILL;

        // Keep the camera's current direction, just place it at the right distance
        const direction = camera.position.clone().sub(sphere.center).normalize();
        if (direction.lengthSq() === 0) direction.set(0, 0, 1);
        camera.position.copy(sphere.center).addScaledVector(direction, distance);
        camera.near = distance / 100;
        camera.far = distance * 100;
        camera.updateProjectionMatrix();

        if (controls) {
            controls.target.copy(sphere.center);
            controls.minDistance = distance * 0.25;
            controls.maxDistance = distance * 4;
            controls.update();
        }
    }, [scene, get, size, url]);

    return <primitive object={scene} />;
}

// Catches GLB load/parse failures so a bad model can't break the page
class ModelErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { failed: false };
    }

    static getDerivedStateFromError() {
        return { failed: true };
    }

    render() {
        if (this.state.failed) {
            return (
                <div className="model-viewer model-viewer-message">
                    Could not load the 3D model for this project.
                </div>
            );
        }
        return this.props.children;
    }
}

function ModelViewer({ modelUrl }) {
    return modelUrl ? <LoadedModelViewer key={modelUrl} modelUrl={modelUrl} /> : null;
}

function LoadedModelViewer({ modelUrl }) {
    const [scene, setScene] = useState(null);
    const [exporting, setExporting] = useState(false);
    const [exportError, setExportError] = useState("");

    async function downloadSTL() {
        if (!scene || exporting) return;
        setExporting(true);
        setExportError("");
        try {
            await new Promise((resolve) => setTimeout(resolve, 30));
            const data = exportSceneSTL(scene);
            const url = URL.createObjectURL(new Blob([data], { type: 'model/stl' }));
            const link = document.createElement('a');
            const name = decodeURIComponent(new URL(modelUrl, window.location.href).pathname.split('/').pop());
            link.href = url;
            link.download = `${name.replace(/\.(glb|gltf)$/i, '') || 'scan'}.stl`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            setTimeout(() => URL.revokeObjectURL(url), 10000);
        } catch (err) {
            setExportError(`Could not export STL: ${err.message}`);
        } finally {
            setExporting(false);
        }
    }

    return (
        <ModelErrorBoundary>
            <button type="button" onClick={downloadSTL} disabled={!scene || exporting}>
                {exporting ? 'Exporting STL...' : 'Export for CAD (STL)'}
            </button>
            <p>CAD-compatible triangle mesh, not a parametric CAD model. Scan meshes may need cleanup; verify scale and units before engineering use.</p>
            {exportError && <p className="form-error" role="alert">{exportError}</p>}
            <div className="model-viewer">
                <Canvas camera={{ position: [0, 0, 4], fov: 45 }}>
                    <ambientLight intensity={0.6} />
                    <directionalLight position={[4, 6, 4]} intensity={1.2} />
                    <Suspense fallback={null}>
                        <Model url={modelUrl} onLoaded={setScene} />
                    </Suspense>
                    <OrbitControls enablePan={false} makeDefault />
                </Canvas>
            </div>
        </ModelErrorBoundary>
    );
}

export default ModelViewer;
