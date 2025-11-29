/**
 * Advanced Patient Search Component
 * Provides comprehensive filtering interface for patient search
 */

import React, { useState } from 'react';
import './AdvancedSearch.css';

export interface SearchFilters {
  search?: string;
  gender?: 'male' | 'female' | 'other' | 'all';
  minAge?: number;
  maxAge?: number;
  dobFrom?: string;
  dobTo?: string;
  city?: string;
  country?: string;
  hasAllergies?: boolean;
  hasMedicalHistory?: boolean;
  createdFrom?: string;
  createdTo?: string;
  updatedFrom?: string;
  updatedTo?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void;
  loading?: boolean;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({ onSearch, loading = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    gender: 'all',
    page: 1,
    pageSize: 50,
    sortBy: 'created_at',
    sortOrder: 'desc',
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFilters((prev) => ({
        ...prev,
        [name]: checked ? true : undefined,
      }));
    } else {
      setFilters((prev) => ({
        ...prev,
        [name]: value || undefined,
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')
    );
    onSearch(cleanFilters);
  };

  const handleReset = () => {
    const resetFilters: SearchFilters = {
      search: '',
      gender: 'all',
      page: 1,
      pageSize: 50,
      sortBy: 'created_at',
      sortOrder: 'desc',
    };
    setFilters(resetFilters);
    onSearch(resetFilters);
  };

  return (
    <div className="advanced-search">
      <form onSubmit={handleSubmit}>
        <div className="search-header">
          <div className="search-bar">
            <input
              type="text"
              name="search"
              placeholder="Search by name, email, phone, or address..."
              value={filters.search || ''}
              onChange={handleInputChange}
              className="search-input"
            />
            <button type="submit" className="search-btn" disabled={loading}>
              {loading ? '⏳' : '🔍'} Search
            </button>
          </div>
          <button
            type="button"
            className="toggle-filters-btn"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '▲' : '▼'} {isExpanded ? 'Hide' : 'Show'} Filters
          </button>
        </div>

        {isExpanded && (
          <div className="filters-panel">
            <div className="filters-grid">
              <div className="filter-group">
                <label htmlFor="gender">Gender</label>
                <select
                  id="gender"
                  name="gender"
                  value={filters.gender}
                  onChange={handleInputChange}
                >
                  <option value="all">All</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="minAge">Min Age</label>
                <input
                  type="number"
                  id="minAge"
                  name="minAge"
                  min="0"
                  max="150"
                  value={filters.minAge || ''}
                  onChange={handleInputChange}
                  placeholder="0"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="maxAge">Max Age</label>
                <input
                  type="number"
                  id="maxAge"
                  name="maxAge"
                  min="0"
                  max="150"
                  value={filters.maxAge || ''}
                  onChange={handleInputChange}
                  placeholder="150"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="city">City</label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={filters.city || ''}
                  onChange={handleInputChange}
                  placeholder="e.g., Paris"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="country">Country</label>
                <input
                  type="text"
                  id="country"
                  name="country"
                  value={filters.country || ''}
                  onChange={handleInputChange}
                  placeholder="e.g., France"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="dobFrom">Date of Birth From</label>
                <input
                  type="date"
                  id="dobFrom"
                  name="dobFrom"
                  value={filters.dobFrom || ''}
                  onChange={handleInputChange}
                />
              </div>

              <div className="filter-group">
                <label htmlFor="dobTo">Date of Birth To</label>
                <input
                  type="date"
                  id="dobTo"
                  name="dobTo"
                  value={filters.dobTo || ''}
                  onChange={handleInputChange}
                />
              </div>

              <div className="filter-group">
                <label htmlFor="sortBy">Sort By</label>
                <select
                  id="sortBy"
                  name="sortBy"
                  value={filters.sortBy}
                  onChange={handleInputChange}
                >
                  <option value="created_at">Created Date</option>
                  <option value="updated_at">Updated Date</option>
                  <option value="first_name">First Name</option>
                  <option value="last_name">Last Name</option>
                  <option value="date_of_birth">Date of Birth</option>
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="sortOrder">Sort Order</label>
                <select
                  id="sortOrder"
                  name="sortOrder"
                  value={filters.sortOrder}
                  onChange={handleInputChange}
                >
                  <option value="asc">Ascending</option>
                  <option value="desc">Descending</option>
                </select>
              </div>

              <div className="filter-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    name="hasAllergies"
                    checked={filters.hasAllergies || false}
                    onChange={handleInputChange}
                  />
                  <span>Has Allergies</span>
                </label>
              </div>

              <div className="filter-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    name="hasMedicalHistory"
                    checked={filters.hasMedicalHistory || false}
                    onChange={handleInputChange}
                  />
                  <span>Has Medical History</span>
                </label>
              </div>
            </div>

            <div className="filter-actions">
              <button type="submit" className="apply-btn" disabled={loading}>
                Apply Filters
              </button>
              <button type="button" className="reset-btn" onClick={handleReset}>
                Reset
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default AdvancedSearch;
