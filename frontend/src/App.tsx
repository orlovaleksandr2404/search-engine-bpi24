import { useState, useCallback, useRef } from 'react';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';
import UploadZone from './components/UploadZone';
import DocumentList from './components/DocumentList';
import type { SearchResult, Document } from './types';

const STORAGE_KEY = 'uploaded_documents';

const loadDocumentsFromStorage = (): Document[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  }
  return [];
};

const saveDocumentsToStorage = (docs: Document[]) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(docs));
};

export default function App() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>(loadDocumentsFromStorage());
  const [isUploading, setIsUploading] = useState(false);

  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [totalPages, setTotalPages] = useState(0);
  const currentQueryRef = useRef(''); 

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setLastQuery(query);
    currentQueryRef.current = query;
    setPage(1);
    setResults([]);
    setHasMore(true);

    try {
      const url = `http://localhost:8000/api/v1/documents/search?q=${encodeURIComponent(query)}&size=3&page=1`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Ошибка при выполнении поиска');
      }
      const data = await response.json();
      setResults(data.results || []);
      setTotalPages(data.total_pages || 0);
      setHasMore(data.page < data.total_pages);
      setPage(data.page || 1);
    } catch (error) {
      console.error('Ошибка поиска:', error);
      setResults([]);
      setHasMore(false);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMore = useCallback(async () => {
    if (isLoadingMore || isLoading || !hasMore || !currentQueryRef.current) return;

    setIsLoadingMore(true);
    const nextPage = page + 1;

    try {
      const url = `http://localhost:8000/api/v1/documents/search?q=${encodeURIComponent(currentQueryRef.current)}&size=10&page=${nextPage}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Ошибка загрузки следующей страницы');
      }
      const data = await response.json();

      setResults(prev => [...prev, ...(data.results || [])]);
      setTotalPages(data.total_pages || 0);
      setHasMore(data.page < data.total_pages);
      setPage(data.page || nextPage);
    } catch (error) {
      console.error('Ошибка загрузки страницы:', error);
      setHasMore(false);
    } finally {
      setIsLoadingMore(false);
    }
  }, [page, hasMore, isLoading, isLoadingMore]);

  const handleFileUpload = async (file: File) => {
    if (file.size > 20 * 1024 * 1024) {
      alert('Файл слишком большой. Максимальный размер — 20 МБ.');
      return;
    }

    const allowedExtensions = ['.pdf', '.docx'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      alert('Поддерживаются только PDF и DOCX файлы.');
      return;
    }

    const newDoc: Document = {
      id: Date.now().toString(),
      file_name: file.name,
      upload_date: new Date().toISOString(),
      status: 'uploading',
    };

    setDocuments(prev => {
      const updated = [...prev, newDoc];
      saveDocumentsToStorage(updated);
      return updated;
    });
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка загрузки');
      }

      await response.json();

      setDocuments(prev => {
        const updated = prev.map(doc =>
          doc.id === newDoc.id ? { ...doc, status: 'ready' } : doc
        );
        saveDocumentsToStorage(updated);
        return updated;
      });
    } catch (error) {
      console.error('Ошибка загрузки:', error);
      setDocuments(prev => {
        const updated = prev.map(doc =>
          doc.id === newDoc.id ? { ...doc, status: 'error' } : doc
        );
        saveDocumentsToStorage(updated);
        return updated;
      });
      alert('Ошибка при загрузке файла: ' + (error as Error).message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>📚 Поиск по документам</h1>
      
      <UploadZone onFileUpload={handleFileUpload} isUploading={isUploading} />
      
      <DocumentList documents={documents} />
      
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      
      <SearchResults 
        results={results} 
        query={lastQuery} 
        onLoadMore={loadMore}
        hasMore={hasMore}
        isLoadingMore={isLoadingMore}
      />
    </div>
  );
}