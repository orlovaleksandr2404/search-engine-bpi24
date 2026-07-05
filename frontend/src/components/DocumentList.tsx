import type { Document } from '../types';

interface DocumentListProps {
  documents: Document[];
}

export default function DocumentList({ documents }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center', 
        color: '#999',
        border: '1px dashed #ddd',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        Нет загруженных документов
      </div>
    );
  }

  const getStatusLabel = (status: Document['status']) => {
    switch (status) {
      case 'uploading': return '⏳ Загрузка...';
      case 'indexing': return '🔄 Индексация...';
      case 'indexed': return '✅ Готово';
      case 'ready': return '✅ Готово';
      case 'error': return '❌ Ошибка';
      default: return status;
    }
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'uploading': return '#ffc107';
      case 'indexing': return '#17a2b8';
      case 'indexed': return '#28a745';
      case 'ready': return '#28a745';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{ marginBottom: '20px' }}>
      <h3 style={{ marginBottom: '12px' }}>📂 Загруженные документы</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="document-item"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 16px',
              backgroundColor: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
            }}
          >
            <span style={{ fontWeight: '500' }}>{doc.file_name}</span>
            <span style={{ fontSize: '12px', color: '#999' }}>
              {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'Дата неизвестна'}
            </span>
            <span style={{ 
              color: getStatusColor(doc.status),
              fontSize: '14px'
            }}>
              {getStatusLabel(doc.status)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}