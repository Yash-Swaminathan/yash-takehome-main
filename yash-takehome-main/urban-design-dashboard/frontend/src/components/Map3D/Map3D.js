import React, { Suspense, useMemo, useRef } from 'react';
import { Canvas, useFrame, extend, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import styled from 'styled-components';
import Building from './Building';

// Extend with OrbitControls
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
extend({ OrbitControls });

const MapContainer = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(to bottom, #87CEEB 0%, #98FB98 50%, #90EE90 100%);
`;

const LocationInfo = styled.div`
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.4;
  z-index: 100;
  
  h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #4A90E2;
  }
  
  p {
    margin: 4px 0;
  }
`;

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: white;
  font-size: 18px;
  gap: 20px;
`;

const Spinner = styled.div`
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const ControlsInfo = styled.div`
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.4;
  z-index: 100;
`;

// Controls component
function Controls() {
  const { camera, gl } = useThree();
  const controlsRef = useRef();
  
  useFrame(() => {
    if (controlsRef.current) {
      controlsRef.current.update();
    }
  });
  
  return (
    <orbitControls
      ref={controlsRef}
      args={[camera, gl.domElement]}
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={50}
      maxDistance={500}
      minPolarAngle={0}
      maxPolarAngle={Math.PI / 2}
    />
  );
}

// Basic lighting setup
function Lighting() {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[100, 100, 100]}
        intensity={1}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-far={200}
        shadow-camera-left={-100}
        shadow-camera-right={100}
        shadow-camera-top={100}
        shadow-camera-bottom={-100}
      />
      <directionalLight position={[-100, 50, -100]} intensity={0.3} />
    </>
  );
}

// Ground plane
function Ground({ bounds }) {
  const groundRef = useRef();
  
  const groundSize = useMemo(() => {
    if (!bounds || bounds.length !== 4) return [200, 200];
    const [latMin, lonMin, latMax, lonMax] = bounds;
    const width = Math.abs(lonMax - lonMin) * 1000;
    const height = Math.abs(latMax - latMin) * 1000;
    return [Math.max(width, 100), Math.max(height, 100)];
  }, [bounds]);
  
  return (
    <mesh ref={groundRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]} receiveShadow>
      <planeGeometry args={groundSize} />
      <meshLambertMaterial color="#90EE90" />
    </mesh>
  );
}

// Buildings container
function BuildingsContainer({ buildings, selectedBuilding, onBuildingClick, bounds }) {
  const buildingsData = useMemo(() => {
    if (!buildings || buildings.length === 0) return [];
    
    // Calculate center for positioning
    const center = bounds && bounds.length === 4 
      ? [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]
      : [buildings[0]?.latitude || 0, buildings[0]?.longitude || 0];
    
    // Use a much smaller scale factor to prevent huge distances
    const scale = 100; // Reduced from 1000
    
    return buildings.map((building, index) => {
      // Use building coordinates if available, otherwise use array index for basic spacing
      let position;
      
      if (building.latitude && building.longitude) {
        position = [
          (building.longitude - center[1]) * scale,
          0,
          -(building.latitude - center[0]) * scale
        ];
      } else {
        // Fallback positioning in a grid if coordinates are missing
        const gridSize = Math.ceil(Math.sqrt(buildings.length));
        const row = Math.floor(index / gridSize);
        const col = index % gridSize;
        const spacing = 20;
        
        position = [
          (col - gridSize / 2) * spacing,
          0,
          (row - gridSize / 2) * spacing
        ];
      }
      
      return {
        ...building,
        position: position
      };
    });
  }, [buildings, bounds]);
  
  return (
    <group>
      {buildingsData.map((building, index) => (
        <Building
          key={building.building_id || `building-${index}`}
          building={building}
          position={building.position}
          isSelected={selectedBuilding?.building_id === building.building_id}
          onClick={() => onBuildingClick(building)}
        />
      ))}
    </group>
  );
}

// Camera setup
function CameraSetup({ bounds }) {
  const { camera } = useThree();
  
  React.useEffect(() => {
    if (bounds && bounds.length === 4) {
      const [latMin, lonMin, latMax, lonMax] = bounds;
      const centerLat = (latMin + latMax) / 2;
      const centerLon = (lonMin + lonMax) / 2;
      const range = Math.max(latMax - latMin, lonMax - lonMin) * 100; // Reduced scale
      
      // Position camera closer for the smaller scale
      camera.position.set(range * 0.8, range * 1.2, range * 0.8);
      camera.lookAt(0, 0, 0);
    } else {
      // Default camera position for sample data
      camera.position.set(80, 120, 80);
      camera.lookAt(0, 0, 0);
    }
  }, [camera, bounds]);
  
  return null;
}

// Loading fallback
function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshBasicMaterial color="gray" />
    </mesh>
  );
}

// Title text (simple mesh text replacement)
function TitleText() {
  return (
    <mesh position={[0, 200, -200]}>
      <boxGeometry args={[100, 20, 5]} />
      <meshBasicMaterial color="white" transparent opacity={0.8} />
    </mesh>
  );
}

function Map3D({ buildings, selectedBuilding, onBuildingClick, isLoading, bounds }) {
  const validBuildings = useMemo(() => {
    return buildings.filter(building => 
      building.latitude && 
      building.longitude && 
      typeof building.latitude === 'number' && 
      typeof building.longitude === 'number'
    );
  }, [buildings]);

  return (
    <MapContainer>
      {isLoading && (
        <LoadingOverlay>
          <Spinner />
          <span>Loading building data...</span>
        </LoadingOverlay>
      )}
      <Canvas 
        camera={{ position: [100, 150, 100], fov: 60, near: 1, far: 2000 }} 
        shadows 
        style={{ background: 'transparent' }}
      >
        <Suspense fallback={<LoadingFallback />}>
          <Lighting />
          <Ground bounds={bounds} />
          <BuildingsContainer 
            buildings={validBuildings} 
            selectedBuilding={selectedBuilding} 
            onBuildingClick={onBuildingClick} 
            bounds={bounds} 
          />
          <CameraSetup bounds={bounds} />
          <TitleText />
          <Controls />
        </Suspense>
      </Canvas>
      <ControlsInfo>
        <strong>Controls:</strong><br />
        • Drag to rotate view<br />
        • Scroll to zoom<br />
        • Right-click + drag to pan<br />
        • Click buildings for details
      </ControlsInfo>
      <LocationInfo>
        <h4>📍 Calgary Location</h4>
        {bounds && bounds.length === 4 ? (
          <>
            <p><strong>Area:</strong> Downtown Calgary</p>
            <p><strong>District:</strong> Beltline/Centre City</p>
            <p><strong>Approx. Coverage:</strong> 3-4 blocks</p>
            <p style={{fontSize: '10px', opacity: 0.8, marginTop: '8px'}}>
              Lat: {bounds[0].toFixed(4)}° - {bounds[2].toFixed(4)}°<br/>
              Lng: {bounds[1].toFixed(4)}° - {bounds[3].toFixed(4)}°
            </p>
          </>
        ) : (
          <>
            <p><strong>Area:</strong> Calgary Sample Data</p>
            <p><strong>District:</strong> Downtown Core</p>
          </>
        )}
      </LocationInfo>
    </MapContainer>
  );
}

export default Map3D; 