import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { Toaster, toast } from 'react-hot-toast';

// Components
import Map3D from './components/Map3D/Map3D';
import QueryInterface from './components/QueryInterface/QueryInterface';
import BuildingPopup from './components/BuildingPopup/BuildingPopup';
import ProjectManager from './components/ProjectManager/ProjectManager';
import UserLogin from './components/UserLogin/UserLogin';

// Services
import apiService from './services/apiClient';

// Styled Components
const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
`;

const Header = styled.header`
  height: 80px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  z-index: 1000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
`;

const Title = styled.h1`
  color: white;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
`;

const HeaderControls = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
`;

const DataSourceSelector = styled.select`
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  
  option {
    background: #333;
    color: white;
  }
`;

const StatusBadge = styled.div`
  background: ${props => props.success ? 'rgba(46, 204, 113, 0.8)' : 'rgba(231, 76, 60, 0.8)'};
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
`;

const SidePanel = styled.div`
  width: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  z-index: 100;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
`;

const DataSourceInfo = styled.div`
  padding: 15px;
  background: rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 12px;
  line-height: 1.4;
  
  h4 {
    margin: 0 0 8px 0;
    color: #333;
  }
  
  p {
    margin: 0;
    color: #666;
  }
`;

const MapContainer = styled.div`
  flex: 1;
  position: relative;
`;

const ControlButton = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  
  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.3);
  }
`;

function App() {
    // State management
    const [user, setUser] = useState(null);
    const [buildings, setBuildings] = useState([]);
    const [selectedBuilding, setSelectedBuilding] = useState(null);
    const [filteredBuildings, setFilteredBuildings] = useState([]);
    const [activeFilters, setActiveFilters] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showProjectManager, setShowProjectManager] = useState(false);
    const [dataSource, setDataSource] = useState('combined'); // 'combined', '3d', 'footprints'
    const [dataStatus, setDataStatus] = useState(null);
    const [zoningData, setZoningData] = useState([]);

    // Calgary downtown bounds (approximately 3-4 blocks)
    const defaultBounds = [51.042, -114.075, 51.048, -114.065];

    // Load initial building data
    useEffect(() => {
        if (user) {
            loadBuildingData();
            loadZoningData();
        }
    }, [user, dataSource]);

    const loadBuildingData = async (refresh = false) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await apiService.getBuildingsInArea(defaultBounds, refresh, dataSource);

            if (response.data.success) {
                setBuildings(response.data.buildings);
                setFilteredBuildings(response.data.buildings);
                setDataStatus({
                    success: true,
                    source: response.data.data_source,
                    cacheStatus: response.data.cache_status,
                    count: response.data.buildings.length
                });
                
                // Show success message with data info
                toast.success(`Loaded ${response.data.buildings.length} buildings from ${response.data.data_source} source`);
            } else {
                throw new Error(response.data.error || 'Failed to load building data');
            }
        } catch (err) {
            setError(err.message);
            setDataStatus({ success: false, error: err.message });
            console.error('Error loading building data:', err);
            toast.error('Failed to load building data');
        } finally {
            setIsLoading(false);
        }
    };

    const loadZoningData = async () => {
        try {
            const response = await apiService.getZoningData(defaultBounds, 100);
            if (response.data.success) {
                setZoningData(response.data.zoning_data);
                toast.success(`Loaded ${response.data.count} zoning districts`);
            }
        } catch (err) {
            console.error('Error loading zoning data:', err);
        }
    };

    const handleDataSourceChange = (newSource) => {
        setDataSource(newSource);
        toast(`Switching to ${newSource} data source...`);
    };

    const test3DBuildings = async () => {
        try {
            setIsLoading(true);
            const response = await apiService.get3DBuildings(defaultBounds, 50);
            if (response.data.success) {
                toast.success(`Found ${response.data.count} 3D buildings with height data`);
                console.log('3D Buildings Sample:', response.data.buildings.slice(0, 3));
            }
        } catch (err) {
            toast.error('Failed to load 3D buildings');
        } finally {
            setIsLoading(false);
        }
    };

    const testPropertyAssessments = async () => {
        try {
            setIsLoading(true);
            const response = await apiService.getPropertyAssessments(null, 20);
            if (response.data.success) {
                toast.success(`Found ${response.data.count} property assessments`);
                console.log('Assessment Sample:', response.data.assessments.slice(0, 3));
            }
        } catch (err) {
            toast.error('Failed to load property assessments');
        } finally {
            setIsLoading(false);
        }
    };

    const handleUserLogin = (userData) => {
        setUser(userData);
    };

    const handleQuerySubmit = async (query) => {
        if (!query.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await apiService.processQuery(query, user?.id, defaultBounds);

            if (response.data.success) {
                setFilteredBuildings(response.data.buildings);
                setActiveFilters(response.data.filters);
                setSelectedBuilding(null); // Clear any selected building
            } else {
                setError(response.data.error || 'Failed to process query');
            }
        } catch (err) {
            setError(err.message);
            console.error('Error processing query:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleBuildingClick = useCallback((building) => {
        setSelectedBuilding(building);
    }, []);

    const handleCloseBuildingPopup = () => {
        setSelectedBuilding(null);
    };

    const handleClearFilters = () => {
        setActiveFilters(null);
        setFilteredBuildings(buildings);
        setSelectedBuilding(null);
    };

    const handleSaveProject = async (projectData) => {
        if (!user || !activeFilters) {
            setError('Please log in and apply filters before saving a project');
            return;
        }

        try {
            const response = await apiService.saveProject(user.id, projectData.name, projectData.description, activeFilters);

            if (response.data.success) {
                return response.data.project;
            } else {
                throw new Error(response.data.error || 'Failed to save project');
            }
        } catch (err) {
            setError(err.message);
            throw err;
        }
    };

    const handleLoadProject = async (project) => {
        try {
            const response = await apiService.loadProject(project.id, true);

            if (response.data.success) {
                setActiveFilters(response.data.filters);
                if (response.data.buildings) {
                    setFilteredBuildings(response.data.buildings);
                }
                setSelectedBuilding(null);
                setShowProjectManager(false);
            } else {
                throw new Error(response.data.error || 'Failed to load project');
            }
        } catch (err) {
            setError(err.message);
            console.error('Error loading project:', err);
        }
    };

    // Show login screen if no user
    if (!user) {
        return (
            <AppContainer>
                <UserLogin onLogin={handleUserLogin} />
                <Toaster position="top-right" />
            </AppContainer>
        );
    }

    return (
        <AppContainer>
            <Header>
                <Title>Urban Design Dashboard - Calgary Open Data</Title>
                <HeaderControls>
                    <span style={{ color: 'white', fontSize: '14px' }}>Data Source:</span>
                    <DataSourceSelector 
                        value={dataSource} 
                        onChange={(e) => handleDataSourceChange(e.target.value)}
                        disabled={isLoading}
                    >
                        <option value="combined">Combined (3D + Footprints)</option>
                        <option value="3d">3D Buildings Only</option>
                        <option value="footprints">Building Footprints</option>
                    </DataSourceSelector>
                    
                    {dataStatus && (
                        <StatusBadge success={dataStatus.success}>
                            {dataStatus.success 
                                ? `${dataStatus.count} buildings (${dataStatus.source})` 
                                : 'Data Error'
                            }
                        </StatusBadge>
                    )}
                    
                    <ControlButton onClick={test3DBuildings} disabled={isLoading}>
                        Test 3D API
                    </ControlButton>
                    
                    <ControlButton onClick={testPropertyAssessments} disabled={isLoading}>
                        Test Assessments
                    </ControlButton>
                    
                    <span style={{ color: 'white', fontSize: '14px' }}>Welcome, {user.username}</span>
                    
                    <ControlButton
                        onClick={() => setShowProjectManager(!showProjectManager)}
                    >
                        Projects
                    </ControlButton>
                    
                    <ControlButton
                        onClick={() => loadBuildingData(true)}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Loading...' : 'Refresh Data'}
                    </ControlButton>
                </HeaderControls>
            </Header>

            <MainContent>
                <SidePanel>
                    <DataSourceInfo>
                        <h4>Calgary Open Data Integration</h4>
                        <p>
                            <strong>Current Source:</strong> {dataSource}<br/>
                            <strong>Buildings:</strong> {filteredBuildings.length} of {buildings.length}<br/>
                            <strong>Zoning Districts:</strong> {zoningData.length}<br/>
                            <strong>Area:</strong> Downtown Calgary (3-4 blocks)
                        </p>
                        <p style={{ marginTop: '8px', fontStyle: 'italic' }}>
                            Buildings are colored by {buildings.some(b => b.assessed_value) ? 'assessed value' : 'building type'}.
                            Height data from Calgary 3D Buildings dataset.
                        </p>
                    </DataSourceInfo>
                    
                    <QueryInterface
                        onQuerySubmit={handleQuerySubmit}
                        onClearFilters={handleClearFilters}
                        activeFilters={activeFilters}
                        isLoading={isLoading}
                        error={error}
                        buildingCount={filteredBuildings.length}
                        totalBuildings={buildings.length}
                    />
                </SidePanel>

                <MapContainer>
                    <Map3D
                        buildings={filteredBuildings}
                        selectedBuilding={selectedBuilding}
                        onBuildingClick={handleBuildingClick}
                        isLoading={isLoading}
                        bounds={defaultBounds}
                    />
                </MapContainer>

                {selectedBuilding && (
                    <BuildingPopup
                        building={selectedBuilding}
                        onClose={handleCloseBuildingPopup}
                    />
                )}

                {showProjectManager && (
                    <ProjectManager
                        user={user}
                        activeFilters={activeFilters}
                        onClose={() => setShowProjectManager(false)}
                        onSaveProject={handleSaveProject}
                        onLoadProject={handleLoadProject}
                    />
                )}
            </MainContent>

            <Toaster position="top-right" />
        </AppContainer>
    );
}

export default App; 