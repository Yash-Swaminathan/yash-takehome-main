import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { Toaster } from 'react-hot-toast';

// Components
import Map3D from './components/Map3D/Map3D';
import QueryInterface from './components/QueryInterface/QueryInterface';
import BuildingPopup from './components/BuildingPopup/BuildingPopup';
import ProjectManager from './components/ProjectManager/ProjectManager';
import UserLogin from './components/UserLogin/UserLogin';

// Services
import { apiClient } from './services/apiClient';

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
  gap: 20px;
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

const MapContainer = styled.div`
  flex: 1;
  position: relative;
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

    // Calgary downtown bounds (approximately 3-4 blocks)
    const defaultBounds = [51.042, -114.075, 51.048, -114.065];

    // Load initial building data
    useEffect(() => {
        if (user) {
            loadBuildingData();
        }
    }, [user]);

    const loadBuildingData = async (refresh = false) => {
        setIsLoading(true);
        setError(null);

        try {
            const boundsStr = defaultBounds.join(',');
            const response = await apiClient.get(`/buildings/area?bounds=${boundsStr}&refresh=${refresh}`);

            if (response.data.success) {
                setBuildings(response.data.buildings);
                setFilteredBuildings(response.data.buildings);
            } else {
                throw new Error(response.data.error || 'Failed to load building data');
            }
        } catch (err) {
            setError(err.message);
            console.error('Error loading building data:', err);
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
            const response = await apiClient.post('/query/process', {
                query: query,
                user_id: user?.id,
                bounds: defaultBounds
            });

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
            const response = await apiClient.post('/projects/save', {
                user_id: user.id,
                name: projectData.name,
                description: projectData.description,
                filters: activeFilters
            });

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
            const response = await apiClient.post(`/projects/${project.id}/load?apply_filters=true`);

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
                <Title>Urban Design Dashboard - Calgary</Title>
                <HeaderControls>
                    <span style={{ color: 'white' }}>Welcome, {user.username}</span>
                    <button
                        onClick={() => setShowProjectManager(!showProjectManager)}
                        style={{
                            background: 'rgba(255, 255, 255, 0.2)',
                            border: '1px solid rgba(255, 255, 255, 0.3)',
                            color: 'white',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            cursor: 'pointer'
                        }}
                    >
                        Projects
                    </button>
                    <button
                        onClick={() => loadBuildingData(true)}
                        disabled={isLoading}
                        style={{
                            background: 'rgba(255, 255, 255, 0.2)',
                            border: '1px solid rgba(255, 255, 255, 0.3)',
                            color: 'white',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            opacity: isLoading ? 0.6 : 1
                        }}
                    >
                        {isLoading ? 'Loading...' : 'Refresh Data'}
                    </button>
                </HeaderControls>
            </Header>

            <MainContent>
                <SidePanel>
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