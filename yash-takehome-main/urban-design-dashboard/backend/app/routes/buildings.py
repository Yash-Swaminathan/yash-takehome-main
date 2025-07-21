from flask import Blueprint, jsonify, request
from app.services.data_fetcher import DataFetcher
from app.services.building_processor import BuildingProcessor
from app.models.building import Building

buildings_bp = Blueprint('buildings', __name__)

@buildings_bp.route('/area', methods=['GET'])
def get_buildings_in_area():
    """Get buildings within a specified area using combined data sources"""
    try:
        # Parse query parameters
        bounds_str = request.args.get('bounds')
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        data_source = request.args.get('source', 'combined')  # footprints, 3d, combined
        
        if not bounds_str:
            return jsonify({'error': 'bounds parameter is required (format: lat_min,lng_min,lat_max,lng_max)'}), 400
        
        try:
            bounds = [float(x) for x in bounds_str.split(',')]
            if len(bounds) != 4:
                raise ValueError("Invalid bounds format")
        except ValueError:
            return jsonify({'error': 'Invalid bounds format. Use: lat_min,lng_min,lat_max,lng_max'}), 400
        
        # Initialize services
        fetcher = DataFetcher()
        processor = BuildingProcessor()
        
        # Check if we should refresh data or use cached data
        if refresh or Building.query.count() == 0:
            # Fetch fresh data from Calgary Open Data API based on source
            if data_source == '3d':
                raw_data = fetcher.fetch_3d_buildings(bounds=tuple(bounds))
            elif data_source == 'footprints':
                raw_data = fetcher.fetch_building_footprints(bounds=tuple(bounds))
            else:  # combined
                raw_data = fetcher.fetch_combined_building_data(bounds=tuple(bounds))
            
            if raw_data:
                # Process and store buildings
                buildings = processor.process_and_store_buildings(raw_data)
            else:
                return jsonify({'error': 'Failed to fetch building data'}), 500
        else:
            # Use cached data from database
            buildings = processor.get_buildings_in_bounds(tuple(bounds))
        
        # Convert to JSON
        buildings_json = [building.to_dict() for building in buildings]
        
        # Get statistics
        stats = processor.get_building_statistics(buildings)
        
        return jsonify({
            'success': True,
            'buildings': buildings_json,
            'statistics': stats,
            'bounds': bounds,
            'data_source': data_source,
            'cache_status': 'fresh' if refresh else 'cached'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/<int:building_id>', methods=['GET'])
def get_building_details(building_id):
    """Get detailed information about a specific building"""
    try:
        building = Building.query.get_or_404(building_id)
        
        return jsonify({
            'success': True,
            'building': building.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/filter', methods=['POST'])
def filter_buildings():
    """Filter buildings based on criteria"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        filter_criteria = data.get('filters')
        bounds = data.get('bounds')
        
        if not filter_criteria:
            return jsonify({'error': 'filters parameter is required'}), 400
        
        processor = BuildingProcessor()
        
        # Get buildings (either all or within bounds)
        if bounds and len(bounds) == 4:
            buildings = processor.get_buildings_in_bounds(tuple(bounds))
        else:
            buildings = Building.query.all()
        
        # Apply filters
        filtered_buildings = processor.filter_buildings(buildings, filter_criteria)
        
        # Convert to JSON
        buildings_json = [building.to_dict() for building in filtered_buildings]
        
        # Get statistics
        stats = processor.get_building_statistics(filtered_buildings)
        
        return jsonify({
            'success': True,
            'buildings': buildings_json,
            'statistics': stats,
            'filter_criteria': filter_criteria,
            'total_matched': len(filtered_buildings)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/refresh', methods=['POST'])
def refresh_building_data():
    """Force refresh of building data from Calgary Open Data API"""
    try:
        data = request.get_json() or {}
        bounds = data.get('bounds')
        
        # Initialize services
        fetcher = DataFetcher()
        processor = BuildingProcessor()
        
        # Fetch fresh data
        if bounds and len(bounds) == 4:
            raw_data = fetcher.fetch_building_footprints(bounds=tuple(bounds))
        else:
            raw_data = fetcher.fetch_building_footprints()
        
        if not raw_data:
            return jsonify({'error': 'Failed to fetch building data from API'}), 500
        
        # Process and store buildings
        buildings = processor.process_and_store_buildings(raw_data)
        
        return jsonify({
            'success': True,
            'message': f'Successfully refreshed {len(buildings)} buildings',
            'buildings_count': len(buildings)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/zoning', methods=['GET'])
def get_zoning_data():
    """Get zoning data for a specified area"""
    try:
        # Parse query parameters
        bounds_str = request.args.get('bounds')
        limit = int(request.args.get('limit', 1000))
        
        if bounds_str:
            try:
                bounds = [float(x) for x in bounds_str.split(',')]
                if len(bounds) != 4:
                    raise ValueError("Invalid bounds format")
                bounds = tuple(bounds)
            except ValueError:
                return jsonify({'error': 'Invalid bounds format. Use: lat_min,lng_min,lat_max,lng_max'}), 400
        else:
            bounds = None
        
        # Fetch zoning data
        fetcher = DataFetcher()
        zoning_data = fetcher.fetch_zoning_data(bounds=bounds, limit=limit)
        
        return jsonify({
            'success': True,
            'zoning_data': zoning_data,
            'bounds': bounds,
            'count': len(zoning_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/assessments', methods=['GET'])
def get_property_assessments():
    """Get property assessment data"""
    try:
        # Parse query parameters
        parcel_ids_str = request.args.get('parcel_ids')
        limit = int(request.args.get('limit', 1000))
        
        parcel_ids = None
        if parcel_ids_str:
            parcel_ids = parcel_ids_str.split(',')
        
        # Fetch assessment data
        fetcher = DataFetcher()
        assessment_data = fetcher.fetch_property_assessments(parcel_ids=parcel_ids, limit=limit)
        
        return jsonify({
            'success': True,
            'assessments': assessment_data,
            'count': len(assessment_data),
            'parcel_ids': parcel_ids
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/3d', methods=['GET'])
def get_3d_buildings():
    """Get 3D building data with height information"""
    try:
        # Parse query parameters
        bounds_str = request.args.get('bounds')
        limit = int(request.args.get('limit', 500))
        
        if bounds_str:
            try:
                bounds = [float(x) for x in bounds_str.split(',')]
                if len(bounds) != 4:
                    raise ValueError("Invalid bounds format")
                bounds = tuple(bounds)
            except ValueError:
                return jsonify({'error': 'Invalid bounds format. Use: lat_min,lng_min,lat_max,lng_max'}), 400
        else:
            bounds = None
        
        # Fetch 3D building data
        fetcher = DataFetcher()
        buildings_3d = fetcher.fetch_3d_buildings(bounds=bounds, limit=limit)
        
        return jsonify({
            'success': True,
            'buildings': buildings_3d,
            'bounds': bounds,
            'count': len(buildings_3d)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@buildings_bp.route('/statistics', methods=['GET'])
def get_building_statistics():
    """Get overall building statistics"""
    try:
        bounds_str = request.args.get('bounds')
        
        processor = BuildingProcessor()
        
        # Get buildings (either all or within bounds)
        if bounds_str:
            try:
                bounds = [float(x) for x in bounds_str.split(',')]
                if len(bounds) == 4:
                    buildings = processor.get_buildings_in_bounds(tuple(bounds))
                else:
                    buildings = Building.query.all()
            except ValueError:
                buildings = Building.query.all()
        else:
            buildings = Building.query.all()
        
        # Get statistics
        stats = processor.get_building_statistics(buildings)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 