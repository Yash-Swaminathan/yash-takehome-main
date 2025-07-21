import React, { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function Building({ building, position, isSelected, onClick }) {
    const meshRef = useRef();
    const [hovered, setHovered] = useState(false);

    // Create building geometry based on footprint and height
    const geometry = useMemo(() => {
        const height = Math.max(building.height || 30, 10); // Minimum height of 10 units

        if (building.footprint && building.footprint.length > 2) {
            // Create shape from footprint coordinates
            const shape = new THREE.Shape();

            building.footprint.forEach((point, index) => {
                const x = point[0] * 1000; // Scale coordinates
                const y = point[1] * 1000;

                if (index === 0) {
                    shape.moveTo(x, y);
                } else {
                    shape.lineTo(x, y);
                }
            });

            // Extrude the shape to create 3D building
            const extrudeSettings = {
                depth: height,
                bevelEnabled: false,
                bevelThickness: 0,
                bevelSize: 0,
                bevelOffset: 0,
                bevelSegments: 1
            };

            return new THREE.ExtrudeGeometry(shape, extrudeSettings);
        } else {
            // Fallback to box geometry if no footprint available
            const width = 20 + Math.random() * 20; // Random width between 20-40
            const depth = 15 + Math.random() * 15; // Random depth between 15-30
            return new THREE.BoxGeometry(width, height, depth);
        }
    }, [building.footprint, building.height]);

    // Determine building color based on type and state
    const material = useMemo(() => {
        let baseColor = '#888888'; // Default gray

        // Color by building type
        switch (building.building_type?.toLowerCase()) {
            case 'commercial':
                baseColor = '#4A90E2'; // Blue
                break;
            case 'residential':
                baseColor = '#7ED321'; // Green
                break;
            case 'industrial':
                baseColor = '#BD10E0'; // Purple
                break;
            case 'mixed use':
                baseColor = '#F5A623'; // Orange
                break;
            default:
                baseColor = '#888888'; // Gray
        }

        // Adjust color for selection/hover state
        let color = baseColor;
        if (isSelected) {
            color = '#FF6B6B'; // Red for selected
        } else if (hovered) {
            color = '#FFD93D'; // Yellow for hovered
        }

        return new THREE.MeshLambertMaterial({
            color: color,
            transparent: true,
            opacity: 0.8
        });
    }, [building.building_type, isSelected, hovered]);

    // Animation for selected buildings
    useFrame(() => {
        if (meshRef.current && isSelected) {
            meshRef.current.rotation.y += 0.01; // Slow rotation
        }
    });

    const handleClick = (event) => {
        event.stopPropagation();
        onClick();
    };

    const handlePointerOver = () => {
        setHovered(true);
        document.body.style.cursor = 'pointer';
    };

    const handlePointerOut = () => {
        setHovered(false);
        document.body.style.cursor = 'default';
    };

    return (
        <mesh
            ref={meshRef}
            position={position}
            geometry={geometry}
            material={material}
            onClick={handleClick}
            onPointerOver={handlePointerOver}
            onPointerOut={handlePointerOut}
            castShadow
            receiveShadow
        />
    );
}

export default Building; 