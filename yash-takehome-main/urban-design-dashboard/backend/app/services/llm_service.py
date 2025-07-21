import json
import re
import requests
import logging
from typing import Dict, List, Optional, Any
from flask import current_app

logger = logging.getLogger(__name__)

class LLMService:
    """Service for processing natural language queries using Hugging Face LLM API"""
    
    def __init__(self):
        self.api_key = current_app.config.get('HUGGINGFACE_API_KEY')
        self.api_url = current_app.config.get('HUGGINGFACE_API_URL')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language query and extract filter criteria
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with filter criteria and metadata
        """
        try:
            # First try LLM API if available
            if self.api_key and self.api_url:
                llm_result = self._query_llm_api(user_query)
                if llm_result:
                    return llm_result
            
            # Fallback to rule-based parsing
            return self._fallback_query_parsing(user_query)
            
        except Exception as e:
            logger.error(f"Error processing query '{user_query}': {e}")
            return self._fallback_query_parsing(user_query)
    
    def _query_llm_api(self, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Query Hugging Face LLM API for intelligent query processing
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Parsed filter criteria or None if failed
        """
        try:
            prompt = self._create_extraction_prompt(user_query)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.1,
                    "return_full_text": False
                }
            }
            
            response = self.session.post(self.api_url, json=payload, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the generated text
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
            else:
                generated_text = str(result)
            
            # Parse the JSON response from LLM
            return self._parse_llm_response(generated_text)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"LLM API request failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM processing failed: {e}")
            return None
    
    def _create_extraction_prompt(self, user_query: str) -> str:
        """
        Create a structured prompt for LLM to extract filter criteria
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
Extract building filter criteria from this query: "{user_query}"

Available attributes: height, zoning, assessed_value, building_type, floors, construction_year
Available operators: >, <, =, >=, <=, contains

Return ONLY a JSON object with:
- attribute: the building property to filter on
- operator: the comparison operator
- value: the filter value (convert to appropriate type)

Examples:
"buildings over 100 feet" -> {{"attribute": "height", "operator": ">", "value": 100}}
"commercial buildings" -> {{"attribute": "building_type", "operator": "contains", "value": "commercial"}}
"buildings worth less than 500000" -> {{"attribute": "assessed_value", "operator": "<", "value": 500000}}
"RC-G zoning" -> {{"attribute": "zoning", "operator": "contains", "value": "RC-G"}}

Query: "{user_query}"
JSON:"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract filter criteria
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed filter criteria
        """
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                filter_data = json.loads(json_str)
                
                # Validate the parsed data
                if self._validate_filter_criteria(filter_data):
                    return {
                        'filters': filter_data,
                        'source': 'llm',
                        'confidence': 0.8,
                        'original_query': response_text
                    }
            
            # If no valid JSON found, fall back to rule-based parsing
            return self._fallback_query_parsing(response_text)
            
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in LLM response: {response_text}")
            return self._fallback_query_parsing(response_text)
    
    def _fallback_query_parsing(self, user_query: str) -> Dict[str, Any]:
        """
        Rule-based fallback for query parsing when LLM is unavailable
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Best-effort filter criteria
        """
        query_lower = user_query.lower()
        
        # Height-based queries
        height_patterns = [
            (r'over (\d+)\s*(?:feet|ft|meters?|m)', '>', 'height'),
            (r'above (\d+)\s*(?:feet|ft|meters?|m)', '>', 'height'),
            (r'taller than (\d+)\s*(?:feet|ft|meters?|m)', '>', 'height'),
            (r'under (\d+)\s*(?:feet|ft|meters?|m)', '<', 'height'),
            (r'below (\d+)\s*(?:feet|ft|meters?|m)', '<', 'height'),
            (r'shorter than (\d+)\s*(?:feet|ft|meters?|m)', '<', 'height'),
        ]
        
        # Value-based queries
        value_patterns = [
            (r'worth more than \$?(\d+(?:,\d{3})*)', '>', 'assessed_value'),
            (r'valued over \$?(\d+(?:,\d{3})*)', '>', 'assessed_value'),
            (r'worth less than \$?(\d+(?:,\d{3})*)', '<', 'assessed_value'),
            (r'valued under \$?(\d+(?:,\d{3})*)', '<', 'assessed_value'),
        ]
        
        # Building type queries
        type_patterns = [
            (r'commercial', '=', 'building_type', 'Commercial'),
            (r'residential', '=', 'building_type', 'Residential'),
            (r'mixed use', '=', 'building_type', 'Mixed Use'),
            (r'industrial', '=', 'building_type', 'Industrial'),
        ]
        
        # Zoning queries
        zoning_patterns = [
            (r'(rc-g|rcg)', 'contains', 'zoning'),
            (r'(cc-x|ccx)', 'contains', 'zoning'),
            (r'(m-cg|mcg)', 'contains', 'zoning'),
        ]
        
        # Check all patterns
        all_patterns = [
            (height_patterns, lambda m: int(m)),
            (value_patterns, lambda m: int(m.replace(',', ''))),
            (type_patterns, lambda m: m),
            (zoning_patterns, lambda m: m.upper()),
        ]
        
        for patterns, value_transformer in all_patterns:
            for pattern_info in patterns:
                if len(pattern_info) == 3:
                    pattern, operator, attribute = pattern_info
                    default_value = None
                else:
                    pattern, operator, attribute, default_value = pattern_info
                
                match = re.search(pattern, query_lower)
                if match:
                    if default_value:
                        value = default_value
                    else:
                        value = value_transformer(match.group(1))
                    
                    return {
                        'filters': {
                            'attribute': attribute,
                            'operator': operator,
                            'value': value
                        },
                        'source': 'fallback',
                        'confidence': 0.6,
                        'original_query': user_query
                    }
        
        # No pattern matched
        return {
            'filters': None,
            'source': 'fallback',
            'confidence': 0.0,
            'original_query': user_query,
            'error': 'Could not parse query'
        }
    
    def _validate_filter_criteria(self, filter_data: Dict) -> bool:
        """
        Validate that filter criteria has required fields and valid values
        
        Args:
            filter_data: Filter criteria to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['attribute', 'operator', 'value']
        if not all(field in filter_data for field in required_fields):
            return False
        
        valid_attributes = [
            'height', 'zoning', 'assessed_value', 'building_type', 
            'floors', 'construction_year', 'land_use'
        ]
        if filter_data['attribute'] not in valid_attributes:
            return False
        
        valid_operators = ['>', '<', '=', '>=', '<=', 'contains']
        if filter_data['operator'] not in valid_operators:
            return False
        
        return True 