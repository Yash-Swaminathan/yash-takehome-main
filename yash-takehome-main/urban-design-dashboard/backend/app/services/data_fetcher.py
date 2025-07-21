import requests
import logging
from typing import List, Dict, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)

class DataFetcher:
    """Service for fetching data from Calgary Open Data API"""
    
    def __init__(self):
        self.base_url = current_app.config.get('CALGARY_OPEN_DATA_BASE_URL', 'https://data.calgary.ca/resource')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Urban-Design-Dashboard/1.0'
        })
    
    def fetch_building_footprints(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 1000) -> List[Dict]:
        """
        Fetch building footprints from Calgary Open Data
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch
            
        Returns:
            List of building footprint records
        """
        try:
            # Calgary Building Footprints dataset
            url = f"{self.base_url}/building-footprints.json"
            
            params = {
                '$limit': limit,
                '$offset': 0
            }
            
            # Add spatial filter if bounds provided
            if bounds:
                lat_min, lon_min, lat_max, lon_max = bounds
                # Use SoQL WHERE clause for spatial filtering
                where_clause = f"within_box(geometry, {lat_max}, {lon_min}, {lat_min}, {lon_max})"
                params['$where'] = where_clause
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {len(data)} building footprints from Calgary Open Data")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching building footprints: {e}")
            return self._get_sample_data()  # Fallback to sample data
        except Exception as e:
            logger.error(f"Unexpected error fetching building footprints: {e}")
            return self._get_sample_data()
    
    def fetch_property_assessments(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch property assessment data from Calgary Open Data
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of property assessment records
        """
        try:
            # Calgary Property Assessments dataset
            url = f"{self.base_url}/property-assessments.json"
            
            params = {
                '$limit': limit,
                '$order': 'assessed_value DESC'
            }
            
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
    
    def fetch_zoning_data(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch zoning data from Calgary Open Data
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of zoning records
        """
        try:
            # Calgary Land Use Bylaw Districts dataset
            url = f"{self.base_url}/land-use-bylaw-districts.json"
            
            params = {
                '$limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {len(data)} zoning records from Calgary Open Data")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching zoning data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching zoning data: {e}")
            return []
    
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
                    "coordinates": [[
                        [-114.0720, 51.0446],
                        [-114.0718, 51.0446],
                        [-114.0718, 51.0448],
                        [-114.0720, 51.0448],
                        [-114.0720, 51.0446]
                    ]]
                }
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
                    "coordinates": [[
                        [-114.0716, 51.0441],
                        [-114.0714, 51.0441],
                        [-114.0714, 51.0443],
                        [-114.0716, 51.0443],
                        [-114.0716, 51.0441]
                    ]]
                }
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
                    "coordinates": [[
                        [-114.0713, 51.0437],
                        [-114.0711, 51.0437],
                        [-114.0711, 51.0439],
                        [-114.0713, 51.0439],
                        [-114.0713, 51.0437]
                    ]]
                }
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
                    "coordinates": [[
                        [-114.0723, 51.0450],
                        [-114.0721, 51.0450],
                        [-114.0721, 51.0452],
                        [-114.0723, 51.0452],
                        [-114.0723, 51.0450]
                    ]]
                }
            }
        ]
        
        logger.info(f"Using sample data: {len(sample_buildings)} buildings")
        return sample_buildings 