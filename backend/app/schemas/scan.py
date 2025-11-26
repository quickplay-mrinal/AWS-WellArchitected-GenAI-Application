from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ScanCreate(BaseModel):
    scan_name: str
    credential_id: int
    regions: Optional[List[str]] = None  # If None, scan all regions

class ScanResponse(BaseModel):
    id: int
    scan_name: str
    status: str
    progress: int
    regions_scanned: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScanDetailResponse(ScanResponse):
    results: Optional[Dict[str, Any]]
    ai_recommendations: Optional[str]
    error_message: Optional[str]
