export type DocumentStatus = 'uploading' | 'indexing' | 'ready' | 'error';

export interface Document {
  id: string;
  file_name: string;
  upload_date: string;
  status: DocumentStatus;
}

export interface SearchResult {
  chunk_id: string;
  file_name: string;
  page: number;
  text: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
}
