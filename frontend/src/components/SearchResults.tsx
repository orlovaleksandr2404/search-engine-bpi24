import { useEffect, useRef, useCallback } from 'react';
import type { SearchResult } from '../types';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  onLoadMore: () => void;
  hasMore: boolean;
  isLoadingMore: boolean;
}

const highlightText = (text: string, query: string) => {
  if (!query.trim()) return text;
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

export default function SearchResults({
  results,
  query,
  onLoadMore,
  hasMore,
  isLoadingMore
}: SearchResultsProps) {
  const observerRef = useRef<HTMLDivElement | null>(null);
  const lastElementRef = useCallback((node: HTMLDivElement | null) => {
    if (isLoadingMore) return;
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        onLoadMore();
      }
    });

    if (node) observerRef.current.observe(node);
  }, [isLoadingMore, hasMore, onLoadMore]);

  if (results.length === 0) {
    return <p style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>
      По вашему запросу ничего не найдено. Попробуйте изменить формулировку.
    </p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
      {results.map((result, index) => {
        const isLast = index === results.length - 1;
        return (
          <div
            key={result.chunk_id}
            ref={isLast ? lastElementRef : null}
            className="result-card"
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
              Релевантность: {Math.min(result.score * 100, 100).toFixed(0)}%
            </div>
          </div>
        );
      })}
      
      {isLoadingMore && (
        <div style={{ textAlign: 'center', padding: '16px', color: '#666' }}>
          Загрузка ещё...
        </div>
      )}
      
      {!hasMore && results.length > 0 && (
        <div style={{ textAlign: 'center', padding: '16px', color: '#999' }}>
          Больше нет результатов
        </div>
      )}
    </div>
  );
}