from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = FastAPI(
    title="Smart Home Temperature API",
    description="API for managing temperature sensors in a smart home",
    version="1.0.0",
    docs_url="/docs"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection configuration
DB_HOST = "postgres"
DB_NAME = "smarthome"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_PORT = "5432"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# Mapping dictionaries
SENSOR_TO_LOCATION = {
    "1": "Living Room",
    "2": "Bedroom",
    "3": "Kitchen"
}

LOCATION_TO_SENSOR = {
    "Living Room": "1",
    "Bedroom": "2",
    "Kitchen": "3"
}

# Sensor models
class SensorCreate(BaseModel):
    location: str
    name: str | None = None  # Optional, defaults to location-based name
    type: str = "temperature"  # Default to temperature sensor
    unit: str = "Celsius"  # Default unit
    status: str = "active"  # Default status

class SensorResponse(BaseModel):
    id: int
    sensor_id: str
    name: str
    type: str
    location: str
    value: float
    unit: str
    status: str
    last_updated: datetime
    created_at: datetime

def generate_unique_sensor_id():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            while True:
                new_id = str(random.randint(5, 999))
                cur.execute("SELECT sensor_id FROM sensors WHERE sensor_id = %s", (new_id,))
                if not cur.fetchone():
                    return new_id
    finally:
        conn.close()

@app.post("/sensors", response_model=SensorResponse)
def create_sensor(sensor: SensorCreate):
    location = sensor.location.strip()
    if not location:
        raise HTTPException(status_code=400, detail="Location cannot be empty")

    # Get sensor_id based on location or generate a unique random ID
    sensor_id = LOCATION_TO_SENSOR.get(location, generate_unique_sensor_id())
    # Set default name based on location if not provided
    name = sensor.name or f"{location} Sensor"

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO sensors (sensor_id, name, type, location, value, unit, status, last_updated, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (sensor_id) DO UPDATE 
                SET location = EXCLUDED.location,
                    name = EXCLUDED.name,
                    type = EXCLUDED.type,
                    unit = EXCLUDED.unit,
                    status = EXCLUDED.status,
                    last_updated = NOW()
                RETURNING *
                """,
                (
                    sensor_id,
                    name,
                    sensor.type,
                    location,
                    round(random.uniform(15.0, 30.0), 1),
                    sensor.unit,
                    sensor.status
                )
            )
            result = cur.fetchone()
            conn.commit()
            return SensorResponse(**result)
    finally:
        conn.close()

@app.get("/sensors", response_model=list[SensorResponse])
def get_all_sensors():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM sensors")
            sensors = cur.fetchall()
            return [SensorResponse(**sensor) for sensor in sensors]
    finally:
        conn.close()

@app.get("/temperature", response_model=SensorResponse)
def get_temperature(location: str = "", sensor_id: str = ""):
    if not location and not sensor_id:
        raise HTTPException(status_code=400, detail="Either location or sensor_id must be provided")

    # If no location is provided, use mapping based on sensor_id
    if not location and sensor_id:
        location = SENSOR_TO_LOCATION.get(sensor_id)

    # If no sensor_id is provided, use mapping based on location
    if not sensor_id and location:
        sensor_id = LOCATION_TO_SENSOR.get(location)

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if location and not sensor_id:
                # Look up sensor by location
                cur.execute("SELECT * FROM sensors WHERE location = %s", (location.strip(),))
                sensor = cur.fetchone()
                if not sensor:
                    # Create a new sensor if location doesn't exist
                    name = f"{location.strip()} Sensor"
                    sensor_id = LOCATION_TO_SENSOR.get(location.strip(), generate_unique_sensor_id())
                    cur.execute(
                        """
                        INSERT INTO sensors (sensor_id, name, type, location, value, unit, status, last_updated, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING *
                        """,
                        (
                            sensor_id,
                            name,
                            "temperature",
                            location.strip(),
                            round(random.uniform(15.0, 30.0), 1),
                            "Celsius",
                            "active"
                        )
                    )
                    sensor = cur.fetchone()
                    conn.commit()
            elif sensor_id and not location:
                # Look up sensor by sensor_id
                cur.execute("SELECT * FROM sensors WHERE sensor_id = %s", (sensor_id,))
                sensor = cur.fetchone()
                if not sensor:
                    raise HTTPException(status_code=400, detail="Invalid sensor_id")
            else:
                # Both provided, verify they match
                cur.execute("SELECT * FROM sensors WHERE sensor_id = %s AND location = %s",
                            (sensor_id, location.strip()))
                sensor = cur.fetchone()
                if not sensor:
                    raise HTTPException(status_code=400, detail="Sensor_id and location do not match any sensor")

            # Update the sensor's value and last_updated timestamp
            new_value = round(random.uniform(15.0, 30.0), 1)
            cur.execute(
                """
                UPDATE sensors
                SET value = %s, last_updated = NOW()
                WHERE sensor_id = %s
                RETURNING *
                """,
                (new_value, sensor["sensor_id"])
            )
            sensor = cur.fetchone()
            conn.commit()
            return SensorResponse(**sensor)
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
