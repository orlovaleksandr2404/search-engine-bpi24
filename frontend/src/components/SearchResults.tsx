import type { SearchResult } from '../types';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
}

const highlightText = (text: string, query: string) => {
  if (!query.trim()) return text;
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

export default function SearchResults({ results, query }: SearchResultsProps) {
  if (results.length === 0) {
    return <p>По вашему запросу ничего не найдено. Попробуйте изменить формулировку.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
      {results.map((result) => (
        <div
          key={result.chunk_id}
          style={{
            border: '1px solid #e0e0e0',
            borderRadius: '12px',
            padding: '16px',
            background: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <strong>{result.file_name}</strong>
            <span style={{ color: '#666', fontSize: '14px' }}>Страница {result.page}</span>
          </div>
          <p
            style={{ margin: '8px 0', lineHeight: '1.6' }}
            dangerouslySetInnerHTML={{ __html: highlightText(result.text, query) }}
          />
          <div style={{ fontSize: '14px', color: '#28a745' }}>
            Релевантность: {(result.score * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}