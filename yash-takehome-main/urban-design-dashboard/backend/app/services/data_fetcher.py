import requests
import logging
from typing import List, Dict, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)

class DataFetcher:
    """Service for fetching data from Calgary Open Data API"""
    
    def __init__(self):
        self.base_url = 'https://data.calgary.ca/resource'
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Urban-Design-Dashboard/1.0'
        })
        
        # Add Socrata App Token if configured
        api_token = current_app.config.get('SOCRATA_APP_TOKEN')
        if api_token:
            self.session.headers['X-App-Token'] = api_token
    
    def fetch_building_footprints(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 1000) -> List[Dict]:
        """
        Fetch building roof outlines (footprints) from Calgary Open Data
        Dataset ID: uc4c-6kbd
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch
            
        Returns:
            List of building footprint records
        """
        try:
            # Calgary Building Roof Outlines dataset
            url = f"{self.base_url}/uc4c-6kbd.geojson"
            
            params = {
                '$limit': limit,
                '$offset': 0
            }
            
            # Add spatial filter if bounds provided
            if bounds:
                lat_min, lon_min, lat_max, lon_max = bounds
                # Use SoQL WHERE clause for spatial filtering
                where_clause = f"within_box(location, {lat_max}, {lon_min}, {lat_min}, {lon_max})"
                params['$where'] = where_clause
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert GeoJSON to our format
            buildings = []
            if 'features' in data:
                for feature in data['features']:
                    building = self._process_footprint_feature(feature)
                    if building:
                        buildings.append(building)
            
            logger.info(f"Fetched {len(buildings)} building footprints from Calgary Open Data")
            return buildings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching building footprints: {e}")
            return self._get_sample_data()  # Fallback to sample data
        except Exception as e:
            logger.error(f"Unexpected error fetching building footprints: {e}")
            return self._get_sample_data()
    
    def fetch_3d_buildings(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 500) -> List[Dict]:
        """
        Fetch 3D buildings with height data from Calgary Open Data
        Dataset ID: cchr-krqg
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch
            
        Returns:
            List of 3D building records
        """
        try:
            url = f"{self.base_url}/cchr-krqg.geojson"
            
            params = {
                '$limit': limit,
                '$select': 'building_id,building_use,height,geometry'
            }
            
            # Add spatial filter if bounds provided
            if bounds:
                lat_min, lon_min, lat_max, lon_max = bounds
                where_clause = f"within_box(geometry, {lat_max}, {lon_min}, {lat_min}, {lon_max})"
                params['$where'] = where_clause
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert GeoJSON to our format
            buildings = []
            if 'features' in data:
                for feature in data['features']:
                    building = self._process_3d_building_feature(feature)
                    if building:
                        buildings.append(building)
            
            logger.info(f"Fetched {len(buildings)} 3D buildings from Calgary Open Data")
            return buildings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching 3D buildings: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching 3D buildings: {e}")
            return []
    
    def fetch_zoning_data(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 1000) -> List[Dict]:
        """
        Fetch land-use districts (zoning) data from Calgary Open Data
        Dataset ID: qe6k-p9nh
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch
            
        Returns:
            List of zoning records
        """
        try:
            url = f"{self.base_url}/qe6k-p9nh.geojson"
            
            params = {
                '$limit': limit
            }
            
            # Add spatial filter if bounds provided
            if bounds:
                lat_min, lon_min, lat_max, lon_max = bounds
                where_clause = f"within_box(geometry, {lat_max}, {lon_min}, {lat_min}, {lon_max})"
                params['$where'] = where_clause
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert GeoJSON to our format
            zoning_data = []
            if 'features' in data:
                for feature in data['features']:
                    zone = self._process_zoning_feature(feature)
                    if zone:
                        zoning_data.append(zone)
            
            logger.info(f"Fetched {len(zoning_data)} zoning records from Calgary Open Data")
            return zoning_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching zoning data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching zoning data: {e}")
            return []
    
    def fetch_property_assessments(self, parcel_ids: Optional[List[str]] = None, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 1000) -> List[Dict]:
        """
        Fetch current-year property assessments from Calgary Open Data
        Dataset ID: 4bsw-nn7w
        
        Args:
            parcel_ids: List of specific parcel IDs to fetch
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box (if location data available)
            limit: Maximum number of records to fetch
            
        Returns:
            List of property assessment records
        """
        try:
            url = f"{self.base_url}/4bsw-nn7w.json"
            
            params = {
                '$limit': limit,
                '$order': 'assessed_value DESC'
            }
            
            # Filter by specific parcel IDs if provided
            if parcel_ids:
                where_clause = ' OR '.join([f"parcel_id='{pid}'" for pid in parcel_ids])
                params['$where'] = where_clause
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {len(data)} property assessments from Calgary Open Data")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property assessments: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching property assessments: {e}")
            return []
    
    def fetch_combined_building_data(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 500) -> List[Dict]:
        """
        Fetch and combine data from multiple sources for comprehensive building information
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch from each source
            
        Returns:
            List of combined building records
        """
        try:
            # Fetch 3D buildings (primary source with height data)
            buildings_3d = self.fetch_3d_buildings(bounds, limit)
            
            # Fetch footprints if 3D data is insufficient
            if len(buildings_3d) < 10:  # Fallback if 3D data is sparse
                footprints = self.fetch_building_footprints(bounds, limit)
                buildings_3d.extend(footprints)
            
            # Fetch zoning data for the area
            zoning_data = self.fetch_zoning_data(bounds, limit)
            
            # Create a mapping of zoning data by geometry (simplified)
            zoning_map = {zone.get('zone_code', 'UNKNOWN'): zone for zone in zoning_data}
            
            # Enhance building data with zoning information
            enhanced_buildings = []
            for building in buildings_3d:
                # Try to match with zoning data (simplified approach)
                # In a real implementation, you'd do proper spatial joins
                building['zoning_data'] = zoning_map.get(building.get('zoning', 'UNKNOWN'), {})
                enhanced_buildings.append(building)
            
            logger.info(f"Combined data: {len(enhanced_buildings)} buildings with zoning information")
            return enhanced_buildings
            
        except Exception as e:
            logger.error(f"Error fetching combined building data: {e}")
            return self._get_sample_data()
    
    def _process_footprint_feature(self, feature: Dict) -> Optional[Dict]:
        """Process a GeoJSON feature from building footprints dataset"""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            return {
                'building_id': properties.get('objectid', str(id(feature))),
                'geometry': geometry,
                'footprint': geometry.get('coordinates', []),
                'building_type': properties.get('building_type', 'Unknown'),
                'address': properties.get('address', ''),
                'height': None,  # Not available in footprints dataset
                'floors': None,
                'zoning': properties.get('zoning', ''),
                'assessed_value': None,
                'land_use': properties.get('land_use', ''),
                'construction_year': properties.get('year_built'),
                'data_source': 'footprints'
            }
        except Exception as e:
            logger.error(f"Error processing footprint feature: {e}")
            return None
    
    def _process_3d_building_feature(self, feature: Dict) -> Optional[Dict]:
        """Process a GeoJSON feature from 3D buildings dataset"""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # Extract coordinates for centroid calculation
            coords = geometry.get('coordinates', [])
            centroid = self._calculate_centroid(coords)
            
            return {
                'building_id': properties.get('building_id', str(id(feature))),
                'geometry': geometry,
                'footprint': coords,
                'latitude': centroid[1] if centroid else None,
                'longitude': centroid[0] if centroid else None,
                'height': properties.get('height'),
                'floors': self._estimate_floors(properties.get('height')),
                'building_type': properties.get('building_use', 'Unknown'),
                'address': properties.get('address', ''),
                'zoning': properties.get('zoning', ''),
                'assessed_value': None,  # Will be joined from assessments
                'land_use': properties.get('building_use', ''),
                'construction_year': properties.get('year_built'),
                'data_source': '3d_buildings'
            }
        except Exception as e:
            logger.error(f"Error processing 3D building feature: {e}")
            return None
    
    def _process_zoning_feature(self, feature: Dict) -> Optional[Dict]:
        """Process a GeoJSON feature from zoning dataset"""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            return {
                'zone_id': properties.get('objectid'),
                'zone_code': properties.get('landuse', ''),
                'zone_name': properties.get('district_name', ''),
                'geometry': geometry,
                'area': properties.get('area'),
                'description': properties.get('description', '')
            }
        except Exception as e:
            logger.error(f"Error processing zoning feature: {e}")
            return None
    
    def _calculate_centroid(self, coordinates) -> Optional[Tuple[float, float]]:
        """Calculate centroid of a polygon"""
        try:
            if not coordinates or not coordinates[0]:
                return None
            
            coords = coordinates[0] if isinstance(coordinates[0][0], list) else coordinates
            
            if len(coords) < 3:
                return None
            
            x_sum = sum(coord[0] for coord in coords)
            y_sum = sum(coord[1] for coord in coords)
            centroid_x = x_sum / len(coords)
            centroid_y = y_sum / len(coords)
            
            return (centroid_x, centroid_y)
        except Exception as e:
            logger.error(f"Error calculating centroid: {e}")
            return None
    
    def _estimate_floors(self, height) -> Optional[int]:
        """Estimate number of floors based on building height"""
        try:
            if height is None:
                return None
            
            height_num = float(height)
            # Assume average floor height of 3.5 meters
            return max(1, int(height_num / 3.5))
        except (ValueError, TypeError):
            return None

    def _get_sample_data(self) -> List[Dict]:
        """
        Return sample building data for development/testing when API is unavailable
        
        Returns:
            List of sample building records
        """
        # Sample data representing 3-4 blocks in downtown Calgary
        sample_buildings = [
            {
                "building_id": "sample_001",
                "address": "123 8 Ave SW, Calgary, AB",
                "latitude": 51.0447,
                "longitude": -114.0719,
                "height": 150.0,
                "floors": 15,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 2500000.0,
                "land_use": "Commercial",
                "construction_year": 2010,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-114.0720, 51.0446],
                        [-114.0718, 51.0446],
                        [-114.0718, 51.0448],
                        [-114.0720, 51.0448],
                        [-114.0720, 51.0446]
                    ]]
                },
                "data_source": "sample"
            },
            {
                "building_id": "sample_002",
                "address": "456 7 Ave SW, Calgary, AB",
                "latitude": 51.0442,
                "longitude": -114.0715,
                "height": 80.0,
                "floors": 8,
                "building_type": "Residential",
                "zoning": "RC-G",
                "assessed_value": 450000.0,
                "land_use": "Residential",
                "construction_year": 2015,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-114.0716, 51.0441],
                        [-114.0714, 51.0441],
                        [-114.0714, 51.0443],
                        [-114.0716, 51.0443],
                        [-114.0716, 51.0441]
                    ]]
                },
                "data_source": "sample"
            },
            {
                "building_id": "sample_003",
                "address": "789 6 Ave SW, Calgary, AB",
                "latitude": 51.0438,
                "longitude": -114.0712,
                "height": 200.0,
                "floors": 20,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 4200000.0,
                "land_use": "Commercial",
                "construction_year": 2008,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-114.0713, 51.0437],
                        [-114.0711, 51.0437],
                        [-114.0711, 51.0439],
                        [-114.0713, 51.0439],
                        [-114.0713, 51.0437]
                    ]]
                },
                "data_source": "sample"
            },
            {
                "building_id": "sample_004",
                "address": "321 9 Ave SW, Calgary, AB",
                "latitude": 51.0451,
                "longitude": -114.0722,
                "height": 60.0,
                "floors": 6,
                "building_type": "Mixed Use",
                "zoning": "M-CG",
                "assessed_value": 750000.0,
                "land_use": "Mixed",
                "construction_year": 2012,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-114.0723, 51.0450],
                        [-114.0721, 51.0450],
                        [-114.0721, 51.0452],
                        [-114.0723, 51.0452],
                        [-114.0723, 51.0450]
                    ]]
                },
                "data_source": "sample"
            }
        ]
        
        logger.info(f"Using sample data: {len(sample_buildings)} buildings")
        return sample_buildings 