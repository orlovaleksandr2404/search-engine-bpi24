import { useState } from 'react';
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

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setLastQuery(query);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/documents/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error('Ошибка при выполнении поиска');
      }
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Ошибка поиска:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

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

      await response.json(); // data не используется, просто ждём ответ

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
      
      <SearchResults results={results} query={lastQuery} />
    </div>
  );
}