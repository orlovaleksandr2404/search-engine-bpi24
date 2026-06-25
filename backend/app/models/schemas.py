from pydantic import BaseModel, UUID4
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: UUID4
    file_name: str
    status: str
    uploaded_at: datetime