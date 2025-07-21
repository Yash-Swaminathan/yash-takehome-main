from flask import Blueprint, jsonify, request
from app.services.llm_service import LLMService
from app.services.building_processor import BuildingProcessor
from app.models.building import Building

llm_bp = Blueprint('llm', __name__)

@llm_bp.route('/process', methods=['POST'])
def process_query():
    """Process natural language query and return filtered buildings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        query = data.get('query')
        user_id = data.get('user_id')
        bounds = data.get('bounds')  # Optional spatial bounds
        
        if not query:
            return jsonify({'error': 'query parameter is required'}), 400
        
        # Process query with LLM service
        llm_service = LLMService()
        query_result = llm_service.process_query(query)
        
        # Check if query processing was successful
        if not query_result.get('filters'):
            return jsonify({
                'success': False,
                'error': query_result.get('error', 'Could not understand the query'),
                'original_query': query,
                'suggestions': [
                    'Try: "buildings over 100 feet"',
                    'Try: "commercial buildings"',
                    'Try: "buildings worth less than $500,000"',
                    'Try: "RC-G zoning"'
                ]
            })
        
        # Get buildings to filter
        processor = BuildingProcessor()
        
        if bounds and len(bounds) == 4:
            buildings = processor.get_buildings_in_bounds(tuple(bounds))
        else:
            buildings = Building.query.all()
        
        # Apply filters
        filtered_buildings = processor.filter_buildings(buildings, query_result['filters'])
        
        # Convert to JSON
        buildings_json = [building.to_dict() for building in filtered_buildings]
        
        # Get statistics
        stats = processor.get_building_statistics(filtered_buildings)
        
        return jsonify({
            'success': True,
            'query': query,
            'filters': query_result['filters'],
            'buildings': buildings_json,
            'statistics': stats,
            'metadata': {
                'source': query_result.get('source'),
                'confidence': query_result.get('confidence'),
                'total_buildings': len(buildings),
                'matched_buildings': len(filtered_buildings)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/parse', methods=['POST'])
def parse_query_only():
    """Parse natural language query without applying to buildings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({'error': 'query parameter is required'}), 400
        
        # Process query with LLM service
        llm_service = LLMService()
        query_result = llm_service.process_query(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'result': query_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/suggestions', methods=['GET'])
def get_query_suggestions():
    """Get sample query suggestions for users"""
    suggestions = [
        {
            'category': 'Height',
            'examples': [
                'buildings over 100 feet',
                'buildings taller than 150 meters',
                'buildings under 50 feet'
            ]
        },
        {
            'category': 'Building Type',
            'examples': [
                'commercial buildings',
                'residential buildings',
                'mixed use buildings',
                'industrial buildings'
            ]
        },
        {
            'category': 'Value',
            'examples': [
                'buildings worth more than $1,000,000',
                'buildings valued under $500,000',
                'properties over $2 million'
            ]
        },
        {
            'category': 'Zoning',
            'examples': [
                'RC-G zoning',
                'CC-X buildings',
                'M-CG zoned properties'
            ]
        },
        {
            'category': 'Age',
            'examples': [
                'buildings built after 2010',
                'buildings constructed before 2000',
                'new buildings'
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })

@llm_bp.route('/validate', methods=['POST'])
def validate_filters():
    """Validate filter criteria format"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        filters = data.get('filters')
        if not filters:
            return jsonify({'error': 'filters parameter is required'}), 400
        
        # Validate filter format
        required_fields = ['attribute', 'operator', 'value']
        valid_attributes = [
            'height', 'zoning', 'assessed_value', 'building_type', 
            'floors', 'construction_year', 'land_use'
        ]
        valid_operators = ['>', '<', '=', '>=', '<=', 'contains']
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in filters:
                errors.append(f'Missing required field: {field}')
        
        # Check valid values
        if 'attribute' in filters and filters['attribute'] not in valid_attributes:
            errors.append(f'Invalid attribute. Valid options: {", ".join(valid_attributes)}')
        
        if 'operator' in filters and filters['operator'] not in valid_operators:
            errors.append(f'Invalid operator. Valid options: {", ".join(valid_operators)}')
        
        is_valid = len(errors) == 0
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'errors': errors,
            'filters': filters
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 