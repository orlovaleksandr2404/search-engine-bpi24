import type { SearchResponse, Document } from '../types';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockSearch = async (query: string): Promise<SearchResponse> => {
  await delay(500);
  return {
    results: Array.from({ length: 10 }, (_, i) => ({
      chunk_id: `chunk-${i}`,
      file_name: `лекция_${i+1}.pdf`,
      page: i + 1,
      text: `Это пример текста с упоминанием "${query}". Здесь может быть полезная информация со страницы ${i+1}. В будущем здесь будут настоящие данные из Elasticsearch.`,
      score: 0.95 - i * 0.03,
    })),
    total: 10,
    page: 1,
    page_size: 10,
  };
};

export const mockDocuments = (): Document[] => {
  return [
    { id: '1', file_name: 'лекция_1.pdf', upload_date: new Date().toISOString(), status: 'ready' },
    { id: '2', file_name: 'лекция_2.pdf', upload_date: new Date().toISOString(), status: 'ready' },
    { id: '3', file_name: 'методичка.docx', upload_date: new Date().toISOString(), status: 'error' },
  ];
};