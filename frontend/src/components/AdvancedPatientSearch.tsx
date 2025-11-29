import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import './AdvancedPatientSearch.css';

interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  address: string;
}

interface SearchFilters {
  query: string;
  gender: string;
  ageMin: string;
  ageMax: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface AdvancedPatientSearchProps {
  token: string;
  onPatientSelect?: (patient: Patient) => void;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AdvancedPatientSearch = ({ token, onPatientSelect }: AdvancedPatientSearchProps) => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    gender: '',
    ageMin: '',
    ageMax: '',
    sortBy: 'last_name',
    sortOrder: 'asc',
  });
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [totalResults, setTotalResults] = useState<number>(0);
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(20);

  const searchPatients = useCallback(
    async (currentPage: number = 1) => {
      setLoading(true);

      try {
        const params: any = {
          skip: (currentPage - 1) * limit,
          limit,
          sort_by: filters.sortBy,
          sort_order: filters.sortOrder,
        };

        if (filters.query) params.search = filters.query;
        if (filters.gender) params.gender = filters.gender;

        const response = await axios.get(`${API_URL}/api/v1/patients/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params,
        });

        if (response.data.items) {
          setPatients(response.data.items);
          setTotalResults(response.data.total);
        } else {
          setPatients(response.data);
          setTotalResults(response.data.length);
        }
      } catch (error) {
        console.error('Search failed:', error);
        setPatients([]);
        setTotalResults(0);
      } finally {
        setLoading(false);
      }
    },
    [filters, limit, token]
  );

  useEffect(() => {
    const debounce = setTimeout(() => {
      searchPatients(page);
    }, 500);

    return () => clearTimeout(debounce);
  }, [filters, page, searchPatients]);

  const handleFilterChange = (key: keyof SearchFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      gender: '',
      ageMin: '',
      ageMax: '',
      sortBy: 'last_name',
      sortOrder: 'asc',
    });
    setPage(1);
  };

  const calculateAge = (dob: string): number => {
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const totalPages = Math.ceil(totalResults / limit);

  return (
    <div className="advanced-patient-search">
      <header className="search-header">
        <div className="search-bar">
          <span className="search-icon" aria-hidden="true">
            🔍
          </span>
          <input
            type="text"
            placeholder="Search by name, email, or phone..."
            value={filters.query}
            onChange={(e) => handleFilterChange('query', e.target.value)}
            className="search-input"
            aria-label="Search patients"
          />
          {filters.query && (
            <button
              onClick={() => handleFilterChange('query', '')}
              className="clear-button"
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`filter-toggle ${showFilters ? 'active' : ''}`}
          aria-expanded={showFilters}
          aria-label="Toggle filters"
        >
          <span>⚙️</span>
          Filters
        </button>
      </header>

      {showFilters && (
        <div className="filters-panel" role="region" aria-label="Search filters">
          <div className="filter-group">
            <label htmlFor="gender-filter">Gender</label>
            <select
              id="gender-filter"
              value={filters.gender}
              onChange={(e) => handleFilterChange('gender', e.target.value)}
            >
              <option value="">All</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="age-min">Min Age</label>
            <input
              id="age-min"
              type="number"
              min="0"
              max="120"
              value={filters.ageMin}
              onChange={(e) => handleFilterChange('ageMin', e.target.value)}
              placeholder="0"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="age-max">Max Age</label>
            <input
              id="age-max"
              type="number"
              min="0"
              max="120"
              value={filters.ageMax}
              onChange={(e) => handleFilterChange('ageMax', e.target.value)}
              placeholder="120"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="sort-by">Sort By</label>
            <select
              id="sort-by"
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
            >
              <option value="last_name">Last Name</option>
              <option value="first_name">First Name</option>
              <option value="date_of_birth">Age</option>
              <option value="created_at">Date Added</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="sort-order">Order</label>
            <select
              id="sort-order"
              value={filters.sortOrder}
              onChange={(e) => handleFilterChange('sortOrder', e.target.value as 'asc' | 'desc')}
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>

          <button onClick={clearFilters} className="clear-filters-btn">
            Clear All Filters
          </button>
        </div>
      )}

      <div className="results-info">
        <span>
          {loading ? 'Searching...' : `${totalResults} patient${totalResults !== 1 ? 's' : ''} found`}
        </span>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
          <p>Loading patients...</p>
        </div>
      ) : patients.length === 0 ? (
        <div className="no-results">
          <span className="icon">🔍</span>
          <h3>No patients found</h3>
          <p>Try adjusting your search criteria</p>
        </div>
      ) : (
        <div className="results-list">
          {patients.map((patient) => (
            <article
              key={patient.id}
              className="patient-card"
              onClick={() => onPatientSelect && onPatientSelect(patient)}
              role="button"
              tabIndex={0}
              onKeyPress={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onPatientSelect && onPatientSelect(patient);
                }
              }}
            >
              <div className="patient-avatar">
                {patient.first_name[0]}
                {patient.last_name[0]}
              </div>

              <div className="patient-info">
                <h3>
                  {patient.first_name} {patient.last_name}
                </h3>
                <div className="patient-details">
                  <span>📧 {patient.email}</span>
                  <span>📱 {patient.phone}</span>
                  <span>
                    🎂 {calculateAge(patient.date_of_birth)} years old
                  </span>
                  <span className="gender-badge">{patient.gender}</span>
                </div>
              </div>

              <div className="patient-actions">
                <button className="view-btn" aria-label={`View ${patient.first_name} ${patient.last_name}`}>
                  View →
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="pagination" role="navigation" aria-label="Pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            aria-label="Previous page"
          >
            ← Previous
          </button>

          <span className="page-info">
            Page {page} of {totalPages}
          </span>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            aria-label="Next page"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default AdvancedPatientSearch;
