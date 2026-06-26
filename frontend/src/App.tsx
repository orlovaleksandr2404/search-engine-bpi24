import { useState } from 'react';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';
import UploadZone from './components/UploadZone';
import DocumentList from './components/DocumentList';
import { mockSearch, mockDocuments } from './services/mockApi';
import type { SearchResult, Document } from './types';

export default function App() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);

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

  setDocuments(prev => [...prev, newDoc]);
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

    const data = await response.json();

    setDocuments(prev =>
      prev.map(doc =>
        doc.id === newDoc.id ? { ...doc, status: 'ready' } : doc
      )
    );
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    setDocuments(prev =>
      prev.map(doc =>
        doc.id === newDoc.id ? { ...doc, status: 'error' } : doc
      )
    );
    alert('Ошибка при загрузке файла: ' + (error as Error).message);
  } finally {
    setIsUploading(false);
  }
};

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>📚 Поиск по документам</h1>
      
      <UploadZone onFileUpload={handleFileUpload} isUploading={isUploading} />
      
      <DocumentList documents={documents} />
      
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      
      <SearchResults results={results} query={lastQuery} />
    </div>
  );
}