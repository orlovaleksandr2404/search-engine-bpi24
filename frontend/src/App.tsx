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

  const handleFileUpload = (file: File) => {

    if (file.size > 20 * 1024 * 1024) {
      alert('Файл слишком большой. Максимальный размер — 20 МБ.');
      return;
    }

    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
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

    setTimeout(() => {
      setDocuments(prev =>
        prev.map(doc =>
          doc.id === newDoc.id ? { ...doc, status: 'indexing' } : doc
        )
      );

      setTimeout(() => {
        setDocuments(prev =>
          prev.map(doc =>
            doc.id === newDoc.id ? { ...doc, status: 'ready' } : doc
          )
        );
        setIsUploading(false);
      }, 1500);
    }, 1500);
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