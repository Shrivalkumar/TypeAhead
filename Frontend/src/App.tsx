import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { Search, X, TrendingUp, AlertCircle, CheckCircle2, Loader2, ArrowUpRight } from 'lucide-react';

// Types
interface SuggestionItem {
  query: string;
  count: number;
}

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error';
}

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [toasts, setToasts] = useState<Toast[]>([]);
  
  // Trending searches mockup (would be fetched from backend in a real app if there was an endpoint)
  const [trending] = useState([
    'iphone 15 pro', 'react tutorial', 'mechanical keyboard', 'fastapi', 'system design'
  ]);

  const searchContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search effect
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!query.trim()) {
        setSuggestions([]);
        setIsOpen(false);
        return;
      }

      setIsLoading(true);
      setIsOpen(true);
      setActiveIndex(-1);

      try {
        const response = await fetch(`${API_BASE_URL}/suggest?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        // Assuming API returns { suggestions: [...] } or array directly
        setSuggestions(data.suggestions || data || []);
      } catch (error) {
        // Fallback to mock data if backend is not running
        console.warn('Backend unavailable, using mock data');
        const mockDb = [
          { query: 'iphone', count: 150000 },
          { query: 'iphone 15', count: 120000 },
          { query: 'iphone 15 pro max', count: 95000 },
          { query: 'iphone 14 case', count: 80000 },
          { query: 'iphone charger', count: 75000 },
          { query: 'react', count: 60000 },
          { query: 'react native', count: 45000 },
          { query: 'react router', count: 30000 },
        ];
        
        const q = query.toLowerCase();
        const filtered = mockDb
          .filter(item => item.query.toLowerCase().startsWith(q))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);
          
        setTimeout(() => {
          setSuggestions(filtered);
        }, 300); // Simulate network latency
      } finally {
        setTimeout(() => setIsLoading(false), 300);
      }
    };

    const timerId = setTimeout(() => {
      fetchSuggestions();
    }, 250);

    return () => clearTimeout(timerId);
  }, [query]);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const handleSearch = async (searchQuery: string) => {
    const q = searchQuery.trim();
    if (!q) return;

    setIsOpen(false);
    setQuery(q);
    inputRef.current?.blur();

    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q })
      });
      
      if (!response.ok) throw new Error('Failed to submit search');
      const data = await response.json();
      showToast(data.message || 'Searched successfully', 'success');
    } catch (error) {
      console.warn('Backend unavailable, showing dummy response');
      showToast('Searched (Mock)', 'success');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === 'Enter') {
        handleSearch(query);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0) {
          handleSearch(suggestions[activeIndex].query);
        } else {
          handleSearch(query);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const highlightMatch = (text: string, match: string) => {
    if (!match.trim()) return text;
    
    // As per requirement, suggestions must start with the prefix
    const q = match.toLowerCase();
    const t = text.toLowerCase();
    
    if (t.startsWith(q)) {
      return (
        <>
          <strong>{text.substring(0, q.length)}</strong>
          {text.substring(q.length)}
        </>
      );
    }
    return text;
  };

  const formatCount = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="container">
      <header className="header">
        <h1>TypeAhead</h1>
        <p>A lightning-fast, highly scalable search suggestion engine</p>
      </header>

      <div className="search-container" ref={searchContainerRef}>
        <div className="search-input-wrapper">
          <Search className="search-icon" size={20} />
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Search for products, keywords, tutorials..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (query.trim()) setIsOpen(true);
            }}
          />
          {query && (
            <button 
              className="clear-button"
              onClick={() => {
                setQuery('');
                setSuggestions([]);
                inputRef.current?.focus();
              }}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
          <button 
            className="search-button"
            onClick={() => handleSearch(query)}
          >
            Search
          </button>
        </div>

        {isOpen && query.trim() && (
          <div className="suggestions-dropdown">
            {isLoading && suggestions.length === 0 ? (
              <div className="loading-state">
                <Loader2 className="spinner" size={24} />
                <span>Finding suggestions...</span>
              </div>
            ) : suggestions.length > 0 ? (
              suggestions.map((item, index) => (
                <div
                  key={item.query}
                  className={`suggestion-item ${index === activeIndex ? 'active' : ''}`}
                  onClick={() => handleSearch(item.query)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <div className="suggestion-content">
                    <Search className="suggestion-icon" size={16} />
                    <span className="suggestion-text">
                      {highlightMatch(item.query, query)}
                    </span>
                  </div>
                  <span className="suggestion-count">
                    {formatCount(item.count)}
                  </span>
                </div>
              ))
            ) : !isLoading ? (
              <div className="empty-state">
                <AlertCircle size={24} className="suggestion-icon" />
                <span>No matching searches found</span>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div className="trending-section">
        <div className="trending-header">
          <TrendingUp className="trending-icon" size={20} />
          <h2>Trending Now</h2>
        </div>
        <div className="trending-tags">
          {trending.map(tag => (
            <div 
              key={tag} 
              className="trending-tag"
              onClick={() => handleSearch(tag)}
            >
              <ArrowUpRight className="trending-trend-icon" size={16} />
              {tag}
            </div>
          ))}
        </div>
      </div>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.type === 'success' ? (
              <CheckCircle2 className="toast-icon" size={20} />
            ) : (
              <AlertCircle className="toast-icon" size={20} />
            )}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
