from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Telemetry API", version="1.0.0")


class TelemetryIn(BaseModel):
    device_id: str = Field(..., min_length=1)
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)


class Telemetry(TelemetryIn):
    id: int
    timestamp: datetime


db: Dict[int, Telemetry] = {}
counter = 0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/telemetry", response_model=Telemetry, status_code=201)
def create_telemetry(item: TelemetryIn):
    global counter
    counter += 1
    record = Telemetry(
        id=counter,
        timestamp=datetime.now(timezone.utc),
        **item.model_dump(),
    )
    db[counter] = record
    return record


@app.get("/telemetry", response_model=List[Telemetry])
def list_telemetry(device_id: Optional[str] = None):
    items = list(db.values())
    if device_id:
        items = [i for i in items if i.device_id == device_id]
    return items


@app.get("/telemetry/{item_id}", response_model=Telemetry)
def get_telemetry(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Record not found")
    return db[item_id]


@app.delete("/telemetry/{item_id}", status_code=204)
def delete_telemetry(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Record not found")
    del db[item_id]