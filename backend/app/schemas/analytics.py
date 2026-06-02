from typing import Optional
from pydantic import BaseModel


class DatasetSummary(BaseModel):
    name: str
    table: str
    row_count: int
    date_range: Optional[str] = None
    description: str
