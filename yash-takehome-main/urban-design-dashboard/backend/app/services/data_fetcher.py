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
                '$offset': 0
                # Removed restrictive $select to get ALL available fields
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Log first record to see all available fields
            if data and len(data) > 0:
                logger.info(f"Available footprint fields: {list(data[0].keys())}")
            
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
                '$limit': limit
                # Removed restrictive $select to get ALL available fields
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Log first record to see all available fields
            if data and len(data) > 0:
                logger.info(f"Available 3D building fields: {list(data[0].keys())}")
            
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
            
            # Log available fields for debugging
            if data and len(data) > 0:
                logger.info(f"Available assessment fields: {list(data[0].keys())}")
            
            # Process assessment data to standardize field names
            processed_data = []
            for record in data:
                processed_record = self._process_assessment_record(record)
                if processed_record:
                    processed_data.append(processed_record)
            
            logger.info(f"Fetched {len(processed_data)} property assessments from Calgary Open Data")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching property assessments: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching property assessments: {e}")
            return []
    
    def _process_assessment_record(self, record: Dict) -> Optional[Dict]:
        """Process a property assessment record to standardize field names"""
        try:
            # Extract assessed value with various possible field names
            assessed_value = self._safe_float(
                record.get('assessed_value') or 
                record.get('total_assessed_value') or
                record.get('current_assessed_value') or
                record.get('property_value') or
                record.get('market_value') or
                record.get('assessment_value')
            )
            
            # Extract address
            address = (
                record.get('address') or 
                record.get('property_address') or
                record.get('civic_address') or
                record.get('full_address')
            )
            
            # Extract construction year
            year_built = self._safe_int(
                record.get('year_built') or
                record.get('construction_year') or
                record.get('year_constructed')
            )
            
            # Extract coordinates if available
            latitude = self._safe_float(record.get('latitude') or record.get('lat'))
            longitude = self._safe_float(record.get('longitude') or record.get('lng'))
            
            return {
                'assessed_value': assessed_value,
                'address': address,
                'year_built': year_built,
                'latitude': latitude,
                'longitude': longitude,
                'parcel_id': record.get('parcel_id') or record.get('id'),
                'raw_record': record
            }
            
        except Exception as e:
            logger.debug(f"Error processing assessment record: {e}")
            return None
    
    def fetch_combined_building_data(self, bounds: Optional[Tuple[float, float, float, float]] = None, limit: int = 500) -> List[Dict]:
        """
        Fetch and combine data from multiple sources for comprehensive building information.
        Intelligent strategy that combines OpenStreetMap + Calgary Open Data for best coverage.
        """
        try:
            logger.info("Starting intelligent data fetch from multiple sources...")
            combined_buildings = []
            building_ids_seen = set()
            
            # Strategy 1: OpenStreetMap for high-quality community data
            logger.info("Fetching from OpenStreetMap...")
            osm_buildings = self.fetch_osm_buildings(bounds, min(limit, 200))
            
            for building in osm_buildings:
                building_id = building['building_id']
                if building_id not in building_ids_seen:
                    combined_buildings.append(building)
                    building_ids_seen.add(building_id)
            
            logger.info(f"Added {len(osm_buildings)} buildings from OpenStreetMap")
            
            # Strategy 2: Calgary 3D Buildings for height data
            logger.info("Fetching from Calgary 3D Buildings...")
            calgary_3d = self.fetch_3d_buildings(bounds, min(limit, 300))
            
            for building in calgary_3d:
                building_id = building['building_id']
                if building_id not in building_ids_seen:
                    combined_buildings.append(building)
                    building_ids_seen.add(building_id)
                else:
                    # Enhance existing OSM building with Calgary data
                    for i, existing in enumerate(combined_buildings):
                        if existing['building_id'] == building_id:
                            # Merge data, preferring Calgary for official attributes
                            if building.get('assessed_value') and not existing.get('assessed_value'):
                                combined_buildings[i]['assessed_value'] = building['assessed_value']
                            if building.get('zoning') and not existing.get('zoning'):
                                combined_buildings[i]['zoning'] = building['zoning']
                            if building.get('construction_year') and not existing.get('construction_year'):
                                combined_buildings[i]['construction_year'] = building['construction_year']
                            break
            
            logger.info(f"Added {len(calgary_3d)} buildings from Calgary 3D, total now: {len(combined_buildings)}")
            
            # Strategy 3: Calgary Building Footprints for additional coverage
            if len(combined_buildings) < 20:  # Only if we need more buildings
                logger.info("Fetching from Calgary Building Footprints...")
                calgary_footprints = self.fetch_building_footprints(bounds, min(limit, 200))
                
                for building in calgary_footprints:
                    building_id = building['building_id']
                    if building_id not in building_ids_seen and len(combined_buildings) < limit:
                        combined_buildings.append(building)
                        building_ids_seen.add(building_id)
                
                logger.info(f"Added additional buildings from footprints, total now: {len(combined_buildings)}")
            
            # Strategy 4: Enhance with Calgary Zoning Data
            logger.info("Enhancing with Calgary zoning data...")
            try:
                zoning_data = self.fetch_zoning_data(bounds, 1000)
                if zoning_data:
                    # Enhance buildings that don't have zoning with spatial zoning data
                    for i, building in enumerate(combined_buildings):
                        if not building.get('zoning') and building.get('latitude') and building.get('longitude'):
                            zoning = self._find_zoning_for_point(building['latitude'], building['longitude'], zoning_data)
                            if zoning:
                                combined_buildings[i]['zoning'] = zoning
                                logger.debug(f"Enhanced building {building['building_id']} with zoning: {zoning}")
                    
                    logger.info("Enhanced buildings with spatial zoning data")
            except Exception as e:
                logger.warning(f"Could not enhance with zoning data: {e}")
            
            # Strategy 5: Enhance with Property Assessment Data
            logger.info("Enhancing with property assessment data...")
            try:
                assessment_data = self.fetch_property_assessments(bounds=bounds, limit=1000)
                if assessment_data:
                    # Match assessment data to buildings by address or coordinates
                    for i, building in enumerate(combined_buildings):
                        if not building.get('assessed_value') or not building.get('construction_year'):
                            assessment = self._find_assessment_for_building(building, assessment_data)
                            if assessment:
                                if not building.get('assessed_value') and assessment.get('assessed_value'):
                                    combined_buildings[i]['assessed_value'] = assessment['assessed_value']
                                if not building.get('construction_year') and assessment.get('year_built'):
                                    combined_buildings[i]['construction_year'] = assessment['year_built']
                                logger.debug(f"Enhanced building {building['building_id']} with assessment data")
                    
                    logger.info("Enhanced buildings with property assessment data")
            except Exception as e:
                logger.warning(f"Could not enhance with assessment data: {e}")
            
            # Strategy 6: Enhanced sample data as final fallback
            if len(combined_buildings) < 5:
                logger.info("Using enhanced sample data as fallback")
                sample_buildings = self._get_sample_data()
                for building in sample_buildings:
                    if len(combined_buildings) < limit:
                        combined_buildings.append(building)
            
            # Sort by assessed value (descending) for better visualization
            combined_buildings.sort(key=lambda x: x.get('assessed_value', 0), reverse=True)
            
            # Log final statistics
            zoning_count = sum(1 for b in combined_buildings if b.get('zoning'))
            construction_year_count = sum(1 for b in combined_buildings if b.get('construction_year'))
            logger.info(f"Final combined dataset: {len(combined_buildings)} buildings")
            logger.info(f"  - With zoning data: {zoning_count}")
            logger.info(f"  - With construction year: {construction_year_count}")
            
            return combined_buildings[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"Error in combined data fetch: {e}")
            logger.info("Falling back to sample data")
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
            
            # Extract construction year from various OSM tags
            construction_year = None
            year_tags = ['start_date', 'construction_start', 'year_built', 'built']
            for tag in year_tags:
                if tags.get(tag):
                    construction_year = self._extract_year(tags[tag])
                    if construction_year:
                        break
            
            # Try to get zoning information from landuse or other tags
            zoning = None
            if 'landuse' in tags:
                zoning = tags['landuse']
            elif 'zoning' in tags:
                zoning = tags['zoning']
            elif 'amenity' in tags:
                zoning = f"amenity:{tags['amenity']}"
            
            # Calculate centroid from geometry with proper coordinate handling
            lat, lng = self._calculate_osm_centroid(element.get('geometry', []))
            
            # Ensure coordinates are valid for Calgary area
            if lat and lng:
                # Validate coordinates are in Calgary area (rough bounds)
                if not (50.8 <= lat <= 51.3 and -114.3 <= lng <= -113.8):
                    logger.warning(f"Building coordinates outside Calgary area: {lat}, {lng}")
                    return None
            else:
                logger.warning("No valid coordinates found for OSM building")
                return None
            
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
                'zoning': zoning,  # Will be None if not available
                'assessed_value': assessed_value,
                'land_use': tags.get('landuse', building_type_normalized),
                'construction_year': construction_year,  # Will be None if not available
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
                          record.get('id') or
                          f"calgary_{id(record)}")
            
            # Extract spatial data
            geometry = record.get('geometry') or record.get('the_geom')
            lat, lng = self._extract_calgary_coordinates(geometry)
            
            # Extract building details with multiple possible field names
            building_type = (record.get('building_use') or 
                           record.get('building_type') or 
                           record.get('bldg_type') or
                           record.get('use_type') or
                           record.get('land_use_type') or
                           'Unknown')
            
            height = self._safe_float(record.get('height') or 
                                     record.get('bldg_height') or 
                                     record.get('max_height'))
            
            floors = self._safe_int(record.get('floors') or 
                                   record.get('levels') or 
                                   record.get('num_floors') or 
                                   record.get('storeys'))
            
            if not floors and height:
                floors = max(1, int(height / 3.5))
            
            # Create realistic address with multiple possible field names
            address = (record.get('address') or 
                      record.get('civic_address') or 
                      record.get('full_address') or
                      record.get('street_address') or
                      record.get('addr_full') or
                      f"{building_id} Calgary, AB")
            
            # Extract zoning with all possible field names used by Calgary
            zoning = (record.get('zoning') or 
                     record.get('zone_class') or
                     record.get('zone_code') or
                     record.get('zoning_class') or
                     record.get('zoning_district') or
                     record.get('zone_category') or
                     record.get('landuse') or
                     record.get('land_use') or
                     record.get('land_use_district'))
            
            # Extract construction year with all possible field names
            construction_year = self._safe_int(record.get('year_built') or 
                                              record.get('construction_year') or
                                              record.get('year_constructed') or
                                              record.get('built_year') or
                                              record.get('date_built') or
                                              record.get('year_completed'))
            
            # If we have a date string, extract year
            if not construction_year:
                for date_field in ['date_built', 'construction_date', 'completion_date']:
                    date_val = record.get(date_field)
                    if date_val:
                        construction_year = self._extract_year(str(date_val))
                        if construction_year:
                            break
            
            # Extract assessed value with multiple possible field names
            assessed_value = self._safe_float(record.get('assessed_value') or 
                                             record.get('total_assessed_value') or
                                             record.get('current_assessed_value') or
                                             record.get('property_value') or
                                             record.get('market_value'))
            
            # Estimate missing values
            if not assessed_value:
                assessed_value = self._estimate_building_value(building_type, height, floors)
            
            # Log what data we found (for debugging)
            logger.debug(f"Calgary building {building_id}: zoning='{zoning}', year={construction_year}, type='{building_type}'")
            
            return {
                'building_id': str(building_id),
                'address': address,
                'latitude': lat,
                'longitude': lng,
                'height': height,
                'floors': floors,
                'building_type': self._normalize_building_type(building_type),
                'zoning': zoning,  # This will now capture more zoning data
                'assessed_value': assessed_value,
                'land_use': building_type,
                'construction_year': construction_year,  # This will now capture more construction years
                'data_source': source,
                'geometry': geometry,
                'raw_record': record  # Keep full record for debugging
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

    def _find_zoning_for_point(self, lat: float, lng: float, zoning_data: List[Dict]) -> Optional[str]:
        """Find zoning classification for a given lat/lng point"""
        try:
            # Simple approach: find the closest zoning district
            # In a full implementation, you'd do proper point-in-polygon testing
            min_distance = float('inf')
            closest_zoning = None
            
            for zone in zoning_data:
                zone_lat = zone.get('latitude') or zone.get('lat')
                zone_lng = zone.get('longitude') or zone.get('lng')
                
                if zone_lat and zone_lng:
                    # Calculate simple distance
                    distance = ((lat - zone_lat) ** 2 + (lng - zone_lng) ** 2) ** 0.5
                    if distance < min_distance:
                        min_distance = distance
                        closest_zoning = zone.get('zone_code') or zone.get('zoning') or zone.get('district_name')
            
            # Only return if reasonably close (within ~0.001 degrees, roughly 100m)
            if min_distance < 0.001 and closest_zoning:
                return closest_zoning
                
        except Exception as e:
            logger.debug(f"Error finding zoning for point: {e}")
        
        return None
    
    def _find_assessment_for_building(self, building: Dict, assessment_data: List[Dict]) -> Optional[Dict]:
        """Find property assessment data for a building"""
        try:
            building_address = building.get('address', '').lower()
            
            # Try to match by address first
            for assessment in assessment_data:
                assessment_address = str(assessment.get('address', '')).lower()
                if assessment_address and building_address:
                    # Simple address matching - look for common parts
                    if any(part in assessment_address for part in building_address.split() if len(part) > 2):
                        return assessment
            
            # If no address match, try coordinate proximity
            building_lat = building.get('latitude')
            building_lng = building.get('longitude')
            
            if building_lat and building_lng:
                min_distance = float('inf')
                closest_assessment = None
                
                for assessment in assessment_data:
                    assessment_lat = assessment.get('latitude') or assessment.get('lat')
                    assessment_lng = assessment.get('longitude') or assessment.get('lng')
                    
                    if assessment_lat and assessment_lng:
                        distance = ((building_lat - assessment_lat) ** 2 + (building_lng - assessment_lng) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_assessment = assessment
                
                # Only return if very close (within ~0.0001 degrees, roughly 10m)
                if min_distance < 0.0001 and closest_assessment:
                    return closest_assessment
                    
        except Exception as e:
            logger.debug(f"Error finding assessment for building: {e}")
        
        return None 