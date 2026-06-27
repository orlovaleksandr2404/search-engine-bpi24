import { useState, useRef } from 'react';

interface UploadZoneProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

export default function UploadZone({ onFileUpload, isUploading }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      onFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className="upload-zone"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      style={{
        border: `2px dashed ${isDragActive ? '#007bff' : '#ccc'}`,
        borderRadius: '12px',
        padding: '40px 20px',
        textAlign: 'center',
        backgroundColor: isDragActive ? '#e3f2fd' : '#f8f9fa',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        marginBottom: '20px',
        opacity: isUploading ? 0.6 : 1,
        pointerEvents: isUploading ? 'none' : 'auto',
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        accept=".pdf,.docx"
      />
      <div style={{ fontSize: '48px', marginBottom: '10px' }}>Загрузить файл</div>
      <h3 style={{ margin: '0 0 8px 0', color: '#333' }}>
        {isDragActive ? '   ' : '  '}
      </h3>
      <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>
         ,    (PDF, DOCX  20 )
      </p>
      {isUploading && (
        <div style={{ marginTop: '16px' }}>
          <div style={{ 
            width: '100%', 
            height: '6px', 
            backgroundColor: '#e0e0e0', 
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{ 
              width: '100%', 
              height: '100%', 
              backgroundColor: '#007bff',
              animation: 'pulse 1.5s infinite'
            }} />
          </div>
          <p style={{ marginTop: '8px', fontSize: '14px', color: '#007bff' }}>
              ...
          </p>
        </div>
      )}
      <style>{`
        @keyframes pulse {
          0% { opacity: 0.6; }
          50% { opacity: 1; }
          100% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}
