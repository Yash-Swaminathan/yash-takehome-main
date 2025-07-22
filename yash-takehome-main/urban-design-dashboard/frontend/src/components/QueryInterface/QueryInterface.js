import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { apiService } from '../../services/apiClient';

const Container = styled.div`
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  overflow: hidden;
`;

const Section = styled.div`
  margin-bottom: 20px;
  flex-shrink: 0;
`;

const SectionTitle = styled.h3`
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
`;

const QueryForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const QueryInput = styled.textarea`
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border: 2px solid #e1e1e1;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s ease;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #667eea;
  }

  &:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button`
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const SubmitButton = styled(Button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
`;

const ClearButton = styled(Button)`
  background: #f8f9fa;
  color: #333;
  border: 1px solid #e1e1e1;

  &:hover:not(:disabled) {
    background: #e9ecef;
  }
`;

const StatusSection = styled.div`
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  font-size: 14px;
`;

const SuccessStatus = styled(StatusSection)`
  background: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.2);
  color: #155724;
`;

const ErrorStatus = styled(StatusSection)`
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.2);
  color: #721c24;
`;

const LoadingStatus = styled(StatusSection)`
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: #0c5460;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const Spinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: #667eea;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const ActiveFilters = styled.div`
  background: rgba(102, 126, 234, 0.1);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
`;

const FilterText = styled.div`
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
`;

const FilterDetails = styled.div`
  font-size: 13px;
  color: #666;
`;

const SuggestionsSection = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
`;

const SuggestionsContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
  
  /* Custom scrollbar styles */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }
`;

const SuggestionCategory = styled.div`
  margin-bottom: 15px;
`;

const CategoryTitle = styled.h4`
  margin: 0 0 8px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
`;

const SuggestionList = styled.ul`
  margin: 0;
  padding: 0;
  list-style: none;
`;

const SuggestionItem = styled.li`
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: all 0.3s ease;

  &:hover {
    background: #e9ecef;
    color: #333;
  }

  &:last-child {
    margin-bottom: 0;
  }
`;

const StatsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-top: 1px solid #e1e1e1;
  margin-top: auto;
  font-size: 13px;
  color: #666;
`;

function QueryInterface({ 
  onQuerySubmit, 
  onClearFilters, 
  activeFilters, 
  isLoading, 
  error, 
  buildingCount,
  totalBuildings 
}) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    // Load query suggestions
    loadSuggestions();
  }, []);

  const loadSuggestions = async () => {
    try {
      const response = await apiService.getQuerySuggestions();
      if (response.data.success) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuerySubmit(query.trim());
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    onQuerySubmit(suggestion);
  };

  const handleClear = () => {
    setQuery('');
    onClearFilters();
  };

  const formatFilterText = (filters) => {
    if (!filters) return '';
    
    const { attribute, operator, value } = filters;
    const operatorText = {
      '>': 'greater than',
      '<': 'less than',
      '=': 'equal to',
      '>=': 'greater than or equal to',
      '<=': 'less than or equal to',
      'contains': 'containing'
    };

    return `${attribute} ${operatorText[operator] || operator} ${value}`;
  };

  return (
    <Container>
      <Section>
        <SectionTitle>Query Buildings</SectionTitle>
        <QueryForm onSubmit={handleSubmit}>
          <QueryInput
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about buildings in natural language...&#10;Examples:&#10;• buildings over 100 feet&#10;• commercial buildings&#10;• buildings worth less than $500,000"
            disabled={isLoading}
          />
          <ButtonGroup>
            <SubmitButton type="submit" disabled={isLoading || !query.trim()}>
              {isLoading ? 'Processing...' : 'Search'}
            </SubmitButton>
            <ClearButton 
              type="button" 
              onClick={handleClear}
              disabled={isLoading}
            >
              Clear
            </ClearButton>
          </ButtonGroup>
        </QueryForm>
      </Section>

      {isLoading && (
        <LoadingStatus>
          <Spinner />
          Processing your query...
        </LoadingStatus>
      )}

      {error && (
        <ErrorStatus>
          <strong>Error:</strong> {error}
        </ErrorStatus>
      )}

      {activeFilters && (
        <Section>
          <ActiveFilters>
            <FilterText>Active Filter:</FilterText>
            <FilterDetails>{formatFilterText(activeFilters)}</FilterDetails>
          </ActiveFilters>
        </Section>
      )}

      <SuggestionsSection>
        <SectionTitle>Query Examples</SectionTitle>
        <SuggestionsContainer>
          {suggestions.map((category, index) => (
            <SuggestionCategory key={index}>
              <CategoryTitle>{category.category}</CategoryTitle>
              <SuggestionList>
                {category.examples.map((example, exampleIndex) => (
                  <SuggestionItem
                    key={exampleIndex}
                    onClick={() => handleSuggestionClick(example)}
                  >
                    {example}
                  </SuggestionItem>
                ))}
              </SuggestionList>
            </SuggestionCategory>
          ))}
        </SuggestionsContainer>
      </SuggestionsSection>

      <StatsContainer>
        <span>
          Showing: {buildingCount.toLocaleString()} buildings
        </span>
        <span>
          Total: {totalBuildings.toLocaleString()}
        </span>
      </StatsContainer>
    </Container>
  );
}

export default QueryInterface; 