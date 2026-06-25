import { useState } from 'react';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';
import { mockSearch } from './services/mockApi';
import type { SearchResult } from './types';

export default function App() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setLastQuery(query);
    try {
      const response = await mockSearch(query);
      setResults(response.results);
    } catch (error) {
      console.error('Ошибка поиска:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>📚 Поиск по документам</h1>
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      <SearchResults results={results} query={lastQuery} />
    </div>
  );
}