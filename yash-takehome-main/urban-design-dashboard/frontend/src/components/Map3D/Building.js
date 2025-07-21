import React, { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function Building({ building, position, isSelected, onClick }) {
    const meshRef = useRef();
    const [hovered, setHovered] = useState(false);

    // Create building geometry based on footprint and height
    const geometry = useMemo(() => {
        // Use height from data, with better scaling for Calgary buildings
        const rawHeight = building.height || (building.floors ? building.floors * 3.5 : 30);
        const height = Math.max(rawHeight * 0.5, 5); // Scale down and ensure minimum height

        // Handle different geometry sources
        let footprintCoords = null;
        
        if (building.geometry && building.geometry.coordinates) {
            // Handle GeoJSON geometry
            const coords = building.geometry.coordinates;
            if (building.geometry.type === 'Polygon' && coords.length > 0) {
                footprintCoords = coords[0]; // Take outer ring
            }
        } else if (building.footprint && Array.isArray(building.footprint)) {
            // Handle direct footprint coordinates
            if (building.footprint.length > 0 && Array.isArray(building.footprint[0])) {
                footprintCoords = building.footprint;
            }
        }

        if (footprintCoords && footprintCoords.length > 2) {
            try {
                // Create shape from footprint coordinates
                const shape = new THREE.Shape();

                footprintCoords.forEach((point, index) => {
                    if (point && point.length >= 2) {
                        // Handle both [lng, lat] and [x, y] formats
                        const x = (point[0] - (building.longitude || 0)) * 100000; // Scale to reasonable size
                        const y = (point[1] - (building.latitude || 0)) * 100000;

                        if (index === 0) {
                            shape.moveTo(x, y);
                        } else {
                            shape.lineTo(x, y);
                        }
                    }
                });

                // Close the shape
                if (footprintCoords.length > 0) {
                    const firstPoint = footprintCoords[0];
                    if (firstPoint && firstPoint.length >= 2) {
                        const x = (firstPoint[0] - (building.longitude || 0)) * 100000;
                        const y = (firstPoint[1] - (building.latitude || 0)) * 100000;
                        shape.lineTo(x, y);
                    }
                }

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
            } catch (error) {
                console.warn('Error creating building geometry from footprint:', error);
                // Fall back to box geometry
            }
        }

        // Fallback to box geometry if no footprint available or if footprint processing failed
        const width = 15 + Math.random() * 10; // Random width between 15-25
        const depth = 10 + Math.random() * 10; // Random depth between 10-20
        return new THREE.BoxGeometry(width, height, depth);
    }, [building.footprint, building.geometry, building.height, building.floors, building.latitude, building.longitude]);

    // Enhanced color system based on multiple factors
    const material = useMemo(() => {
        let baseColor = '#888888'; // Default gray
        let colorMode = 'type'; // Default to building type coloring

        // Check if we have assessed value for value-based coloring
        if (building.assessed_value && building.assessed_value > 0) {
            colorMode = 'value';
            const value = building.assessed_value;
            
            // Color scale based on assessed value ranges (Calgary-specific)
            if (value > 5000000) {
                baseColor = '#FF0000'; // Red for very high value (>5M)
            } else if (value > 2000000) {
                baseColor = '#FF6600'; // Orange for high value (2-5M)
            } else if (value > 1000000) {
                baseColor = '#FFCC00'; // Yellow for medium-high value (1-2M)
            } else if (value > 500000) {
                baseColor = '#66FF66'; // Light green for medium value (500k-1M)
            } else {
                baseColor = '#0066FF'; // Blue for lower value (<500k)
            }
        } else {
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
                case 'mixed':
                    baseColor = '#F5A623'; // Orange
                    break;
                default:
                    // Color by zoning if available
                    if (building.zoning) {
                        const zoning = building.zoning.toLowerCase();
                        if (zoning.includes('residential') || zoning.includes('r-')) {
                            baseColor = '#7ED321'; // Green for residential
                        } else if (zoning.includes('commercial') || zoning.includes('c-')) {
                            baseColor = '#4A90E2'; // Blue for commercial
                        } else if (zoning.includes('industrial') || zoning.includes('i-')) {
                            baseColor = '#BD10E0'; // Purple for industrial
                        } else {
                            baseColor = '#888888'; // Gray for unknown
                        }
                    } else {
                        baseColor = '#888888'; // Gray for unknown
                    }
            }
        }

        // Adjust color for selection/hover state
        let color = baseColor;
        let opacity = 0.8;
        
        if (isSelected) {
            color = '#FF6B6B'; // Red for selected
            opacity = 1.0;
        } else if (hovered) {
            color = '#FFD93D'; // Yellow for hovered
            opacity = 0.9;
        }

        return new THREE.MeshLambertMaterial({
            color: color,
            transparent: true,
            opacity: opacity
        });
    }, [building.building_type, building.assessed_value, building.zoning, isSelected, hovered]);

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