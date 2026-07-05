import { useState } from 'react';

interface SearchBarProps {

  /**
   * Функция, вызываемая при отправке формы поиска.
   * @param query - Поисковый запрос.
   */
  onSearch: (query: string) => void;
  /** Флаг, указывающий, выполняется ли сейчас поиск (блокирует кнопку). */
  isLoading: boolean;
}

/**
 * Компонент строки поиска.
 * Содержит поле ввода и кнопку для отправки запроса.
 */
export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');

  /**
   * Обработчик отправки формы.
   * Предотвращает перезагрузку страницы и вызывает onSearch, если запрос не пустой.
   * @param e - Событие отправки формы.
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form className="search-form" onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', margin: '20px 0' }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Введите запрос..."
        style={{
          flex: 1,
          padding: '12px 16px',
          fontSize: '16px',
          border: '1px solid #ccc',
          borderRadius: '8px',
          outline: 'none',
        }}
      />
      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          background: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          opacity: isLoading || !query.trim() ? 0.6 : 1,
        }}
      >
        {isLoading ? 'Поиск...' : 'Найти'}
      </button>
    </form>
  );
}
