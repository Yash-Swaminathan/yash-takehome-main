import requests
import logging
from typing import List, Dict, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)

class DataFetcher:
    """Service for fetching data from Calgary Open Data API and OpenStreetMap"""
    
    def __init__(self):
        self.base_url = 'https://data.calgary.ca/resource'
        self.osm_url = 'https://overpass-api.de/api/interpreter'
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Urban-Design-Dashboard/1.0'
        })
        
        # Add Socrata App Token if configured
        api_token = current_app.config.get('SOCRATA_APP_TOKEN')
        if api_token:
            self.session.headers['X-App-Token'] = api_token
    
    def fetch_osm_buildings(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 500) -> List[Dict]:
        """
        Fetch building data from OpenStreetMap using Overpass API
        
        Args:
            bounds: (lat_min, lon_min, lat_max, lon_max) bounding box
            limit: Maximum number of records to fetch
            
        Returns:
            List of building records from OSM
        """
        try:
            # Default to Calgary downtown if no bounds provided
            if not bounds:
                bounds = (51.042, -114.075, 51.048, -114.065)
            
            lat_min, lon_min, lat_max, lon_max = bounds
            
            # Overpass QL query for buildings with detailed attributes
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["building"]({lat_min},{lon_min},{lat_max},{lon_max});
              relation["building"]({lat_min},{lon_min},{lat_max},{lon_max});
            );
            out geom meta;
            """
            
            response = self.session.post(self.osm_url, data=overpass_query, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process OSM data
            buildings = []
            elements = data.get('elements', [])
            
            for element in elements[:limit]:  # Limit results
                building = self._process_osm_element(element)
                if building:
                    buildings.append(building)
            
            logger.info(f"Fetched {len(buildings)} buildings from OpenStreetMap")
            return buildings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OSM buildings: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching OSM buildings: {e}")
            return []
    
    def fetch_building_footprints(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 1000) -> List[Dict]:
        """
        Fetch building roof outlines (footprints) from Calgary Open Data
        Dataset ID: uc4c-6kbd
        """
        try:
            # Try OSM first for better data quality
            osm_buildings = self.fetch_osm_buildings(bounds, min(limit, 100))
            if len(osm_buildings) > 5:
                return osm_buildings
            
            # Fallback to Calgary Open Data
            url = f"{self.base_url}/uc4c-6kbd.json"  # Try JSON first
            
            params = {
                '$limit': limit,
                '$offset': 0,
                '$select': 'objectid,address,building_type,year_built,zoning,geometry'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process Calgary data
            buildings = []
            for record in data:
                building = self._process_calgary_record(record, 'footprints')
                if building:
                    buildings.append(building)
            
            logger.info(f"Fetched {len(buildings)} building footprints from Calgary Open Data")
            return buildings if buildings else self._get_sample_data()
            
        except Exception as e:
            logger.error(f"Error fetching building footprints: {e}")
            return self._get_sample_data()
    
    def fetch_3d_buildings(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 500) -> List[Dict]:
        """
        Fetch 3D buildings with height data from Calgary Open Data
        Dataset ID: cchr-krqg
        """
        try:
            url = f"{self.base_url}/cchr-krqg.json"  # Try JSON format
            
            params = {
                '$limit': limit,
                '$select': 'building_id,building_use,height,address,zoning,geometry'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process Calgary 3D data
            buildings = []
            for record in data:
                building = self._process_calgary_record(record, '3d_buildings')
                if building:
                    buildings.append(building)
            
            logger.info(f"Fetched {len(buildings)} 3D buildings from Calgary Open Data")
            return buildings if buildings else []
            
        except Exception as e:
            logger.error(f"Error fetching 3D buildings: {e}")
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
        """
        try:
            # Primary: Try OpenStreetMap for high-quality data
            osm_buildings = self.fetch_osm_buildings(bounds, min(limit, 100))
            
            if len(osm_buildings) > 10:
                logger.info(f"Using OSM data: {len(osm_buildings)} buildings")
                return osm_buildings
            
            # Secondary: Try Calgary 3D buildings
            calgary_3d = self.fetch_3d_buildings(bounds, limit)
            if len(calgary_3d) > 5:
                logger.info(f"Using Calgary 3D data: {len(calgary_3d)} buildings")
                return calgary_3d
            
            # Tertiary: Try Calgary footprints
            calgary_footprints = self.fetch_building_footprints(bounds, limit)
            if len(calgary_footprints) > 5:
                logger.info(f"Using Calgary footprints: {len(calgary_footprints)} buildings")
                return calgary_footprints
            
            # Fallback: Enhanced sample data
            logger.info("Using enhanced sample data")
            return self._get_sample_data()
            
        except Exception as e:
            logger.error(f"Error fetching combined building data: {e}")
            return self._get_sample_data()
    
    def _process_osm_element(self, element: Dict) -> Optional[Dict]:
        """Process an OpenStreetMap element into our building format"""
        try:
            tags = element.get('tags', {})
            
            # Extract building information
            building_type = tags.get('building', 'unknown')
            if building_type == 'yes':
                building_type = tags.get('building:use', 'Unknown')
            
            # Normalize building type
            building_type_normalized = self._normalize_building_type(building_type)
            
            # Extract height information
            height = None
            floors = None
            
            if 'height' in tags:
                try:
                    height_str = tags['height'].replace('m', '').replace(' ', '')
                    height = float(height_str)
                except:
                    pass
            
            if 'building:levels' in tags:
                try:
                    floors = int(tags['building:levels'])
                    if not height and floors:
                        height = floors * 3.5  # Estimate height
                except:
                    pass
            
            # Calculate centroid from geometry
            lat, lng = self._calculate_osm_centroid(element.get('geometry', []))
            
            # Create address from available data
            address = self._create_osm_address(tags, lat, lng)
            
            # Estimate assessed value based on building type and size
            assessed_value = self._estimate_building_value(building_type_normalized, height, floors)
            
            return {
                'building_id': f"osm_{element.get('id', 'unknown')}",
                'address': address,
                'latitude': lat,
                'longitude': lng,
                'height': height,
                'floors': floors,
                'building_type': building_type_normalized,
                'zoning': tags.get('landuse', ''),
                'assessed_value': assessed_value,
                'land_use': tags.get('landuse', building_type_normalized),
                'construction_year': self._extract_year(tags.get('start_date', '')),
                'data_source': 'openstreetmap',
                'osm_amenity': tags.get('amenity', ''),
                'osm_name': tags.get('name', ''),
                'geometry': element.get('geometry', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing OSM element: {e}")
            return None
    
    def _process_calgary_record(self, record: Dict, source: str) -> Optional[Dict]:
        """Process a Calgary Open Data record into our building format"""
        try:
            # Extract ID
            building_id = (record.get('building_id') or 
                          record.get('objectid') or 
                          f"calgary_{id(record)}")
            
            # Extract spatial data
            geometry = record.get('geometry')
            lat, lng = self._extract_calgary_coordinates(geometry)
            
            # Extract building details
            building_type = (record.get('building_use') or 
                           record.get('building_type') or 
                           'Unknown')
            
            height = self._safe_float(record.get('height'))
            floors = self._safe_int(record.get('floors') or record.get('levels'))
            
            if not floors and height:
                floors = max(1, int(height / 3.5))
            
            # Create realistic address
            address = (record.get('address') or 
                      record.get('civic_address') or 
                      f"{building_id} Calgary, AB")
            
            # Extract other attributes
            zoning = record.get('zoning', '')
            assessed_value = self._safe_float(record.get('assessed_value'))
            construction_year = self._safe_int(record.get('year_built'))
            
            # Estimate missing values
            if not assessed_value:
                assessed_value = self._estimate_building_value(building_type, height, floors)
            
            return {
                'building_id': str(building_id),
                'address': address,
                'latitude': lat,
                'longitude': lng,
                'height': height,
                'floors': floors,
                'building_type': self._normalize_building_type(building_type),
                'zoning': zoning,
                'assessed_value': assessed_value,
                'land_use': building_type,
                'construction_year': construction_year,
                'data_source': source,
                'geometry': geometry
            }
            
        except Exception as e:
            logger.error(f"Error processing Calgary record: {e}")
            return None
    
    def _calculate_osm_centroid(self, geometry: List) -> Tuple[Optional[float], Optional[float]]:
        """Calculate centroid from OSM geometry"""
        try:
            if not geometry:
                return None, None
            
            lats = [point.get('lat') for point in geometry if point.get('lat')]
            lons = [point.get('lon') for point in geometry if point.get('lon')]
            
            if lats and lons:
                return sum(lats) / len(lats), sum(lons) / len(lons)
                
        except Exception as e:
            logger.error(f"Error calculating OSM centroid: {e}")
            
        return None, None
    
    def _extract_calgary_coordinates(self, geometry) -> Tuple[Optional[float], Optional[float]]:
        """Extract coordinates from Calgary geometry data"""
        try:
            if isinstance(geometry, dict):
                if 'coordinates' in geometry:
                    coords = geometry['coordinates']
                    if isinstance(coords, list) and len(coords) >= 2:
                        return coords[1], coords[0]  # lat, lng
                        
        except Exception as e:
            logger.error(f"Error extracting Calgary coordinates: {e}")
            
        return None, None
    
    def _create_osm_address(self, tags: Dict, lat: float, lng: float) -> str:
        """Create a realistic address from OSM tags"""
        if tags.get('addr:full'):
            return tags['addr:full']
        
        address_parts = []
        
        if tags.get('addr:housenumber'):
            address_parts.append(tags['addr:housenumber'])
        
        if tags.get('addr:street'):
            address_parts.append(tags['addr:street'])
        elif tags.get('name'):
            address_parts.append(f"near {tags['name']}")
        
        if not address_parts and lat and lng:
            # Generate address based on coordinates in Calgary
            street_num = int((lat - 51.0) * 10000) % 999 + 1
            avenue_num = int((lng + 114.0) * 100) % 20 + 1
            address_parts = [str(street_num), f"{avenue_num} Ave SW"]
        
        address_parts.append("Calgary, AB")
        return " ".join(address_parts)
    
    def _estimate_building_value(self, building_type: str, height: float, floors: int) -> float:
        """Estimate building assessed value based on characteristics"""
        try:
            base_value = 300000  # Base value
            
            # Type multiplier
            type_multipliers = {
                'Commercial': 3.0,
                'Residential': 1.0,
                'Mixed Use': 2.0,
                'Industrial': 1.5,
                'retail': 2.5,
                'office': 3.5,
                'apartments': 1.2,
                'hotel': 2.8
            }
            
            multiplier = type_multipliers.get(building_type, 1.0)
            
            # Height/floor bonus
            if height:
                multiplier *= (1 + height / 100)
            elif floors:
                multiplier *= (1 + floors / 10)
            
            estimated_value = base_value * multiplier
            
            # Add some randomness
            import random
            estimated_value *= (0.8 + random.random() * 0.4)
            
            return round(estimated_value, -3)  # Round to nearest thousand
            
        except:
            return 350000.0  # Default value
    
    def _normalize_building_type(self, building_type: str) -> str:
        """Normalize building type to standard categories"""
        if not building_type:
            return "Unknown"
        
        building_type_lower = building_type.lower()
        
        # Map various types to standard categories
        if any(term in building_type_lower for term in ['commercial', 'office', 'retail', 'store', 'shop']):
            return "Commercial"
        elif any(term in building_type_lower for term in ['residential', 'apartment', 'apartments', 'condo', 'house', 'housing']):
            return "Residential"
        elif any(term in building_type_lower for term in ['industrial', 'warehouse', 'manufacturing', 'factory']):
            return "Industrial"
        elif any(term in building_type_lower for term in ['mixed', 'multi']):
            return "Mixed Use"
        elif any(term in building_type_lower for term in ['hotel', 'motel']):
            return "Commercial"
        elif any(term in building_type_lower for term in ['school', 'hospital', 'church', 'university']):
            return "Institutional"
        else:
            return building_type.title()
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        try:
            if date_str and len(date_str) >= 4:
                return int(date_str[:4])
        except:
            pass
        return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if value is not None:
                return float(value)
        except (ValueError, TypeError):
            pass
        return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer"""
        try:
            if value is not None:
                return int(float(value))
        except (ValueError, TypeError):
            pass
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
    
    def _get_sample_data(self) -> List[Dict]:
        """
        Return sample building data for development/testing when API is unavailable
        
        Returns:
            List of sample building records representing downtown Calgary
        """
        # Expanded sample data representing multiple blocks in downtown Calgary
        sample_buildings = [
            # 8th Avenue SW - Commercial core
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
            },
            # Additional buildings for more realistic coverage
            {
                "building_id": "sample_005",
                "address": "234 8 Ave SW, Calgary, AB",
                "latitude": 51.0445,
                "longitude": -114.0716,
                "height": 120.0,
                "floors": 12,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 1800000.0,
                "land_use": "Commercial",
                "construction_year": 2005,
                "data_source": "sample"
            },
            {
                "building_id": "sample_006",
                "address": "567 7 Ave SW, Calgary, AB",
                "latitude": 51.0443,
                "longitude": -114.0710,
                "height": 95.0,
                "floors": 9,
                "building_type": "Residential",
                "zoning": "RC-G",
                "assessed_value": 520000.0,
                "land_use": "Residential",
                "construction_year": 2018,
                "data_source": "sample"
            },
            {
                "building_id": "sample_007",
                "address": "890 6 Ave SW, Calgary, AB",
                "latitude": 51.0439,
                "longitude": -114.0708,
                "height": 180.0,
                "floors": 18,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 3200000.0,
                "land_use": "Commercial",
                "construction_year": 2012,
                "data_source": "sample"
            },
            {
                "building_id": "sample_008",
                "address": "432 9 Ave SW, Calgary, AB",
                "latitude": 51.0450,
                "longitude": -114.0718,
                "height": 75.0,
                "floors": 7,
                "building_type": "Mixed Use",
                "zoning": "M-CG",
                "assessed_value": 680000.0,
                "land_use": "Mixed",
                "construction_year": 2014,
                "data_source": "sample"
            },
            {
                "building_id": "sample_009",
                "address": "155 8 Ave SW, Calgary, AB",
                "latitude": 51.0446,
                "longitude": -114.0714,
                "height": 65.0,
                "floors": 6,
                "building_type": "Residential",
                "zoning": "RC-G",
                "assessed_value": 390000.0,
                "land_use": "Residential",
                "construction_year": 2016,
                "data_source": "sample"
            },
            {
                "building_id": "sample_010",
                "address": "678 7 Ave SW, Calgary, AB",
                "latitude": 51.0441,
                "longitude": -114.0706,
                "height": 250.0,
                "floors": 25,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 5800000.0,
                "land_use": "Commercial",
                "construction_year": 2019,
                "data_source": "sample"
            },
            {
                "building_id": "sample_011",
                "address": "234 6 Ave SW, Calgary, AB",
                "latitude": 51.0437,
                "longitude": -114.0720,
                "height": 105.0,
                "floors": 10,
                "building_type": "Mixed Use",
                "zoning": "M-CG",
                "assessed_value": 920000.0,
                "land_use": "Mixed",
                "construction_year": 2013,
                "data_source": "sample"
            },
            {
                "building_id": "sample_012",
                "address": "789 9 Ave SW, Calgary, AB",
                "latitude": 51.0452,
                "longitude": -114.0713,
                "height": 45.0,
                "floors": 4,
                "building_type": "Residential",
                "zoning": "RC-G",
                "assessed_value": 280000.0,
                "land_use": "Residential",
                "construction_year": 2020,
                "data_source": "sample"
            },
            {
                "building_id": "sample_013",
                "address": "345 8 Ave SW, Calgary, AB",
                "latitude": 51.0448,
                "longitude": -114.0711,
                "height": 140.0,
                "floors": 14,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 2100000.0,
                "land_use": "Commercial",
                "construction_year": 2009,
                "data_source": "sample"
            },
            {
                "building_id": "sample_014",
                "address": "567 6 Ave SW, Calgary, AB",
                "latitude": 51.0440,
                "longitude": -114.0704,
                "height": 85.0,
                "floors": 8,
                "building_type": "Residential",
                "zoning": "RC-G",
                "assessed_value": 465000.0,
                "land_use": "Residential",
                "construction_year": 2017,
                "data_source": "sample"
            },
            {
                "building_id": "sample_015",
                "address": "890 9 Ave SW, Calgary, AB",
                "latitude": 51.0453,
                "longitude": -114.0709,
                "height": 35.0,
                "floors": 3,
                "building_type": "Commercial",
                "zoning": "CC-X",
                "assessed_value": 320000.0,
                "land_use": "Commercial",
                "construction_year": 2011,
                "data_source": "sample"
            }
        ]
        
        logger.info(f"Using sample data: {len(sample_buildings)} buildings")
        return sample_buildings 