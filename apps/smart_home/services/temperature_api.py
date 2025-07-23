from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import psycopg2
from psycopg2.extras import RealDictCursor

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
DB_NAME = "smart_home"
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

# Sensor model
class SensorCreate(BaseModel):
    location: str

class SensorResponse(BaseModel):
    sensor_id: str
    location: str
    temperature: float

# Mapping dictionaries for sensor_id and location
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

def generate_unique_sensor_id():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            while True:
                # Generate a random numeric ID between 5 and 999
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

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO sensors (sensor_id, location) VALUES (%s, %s) ON CONFLICT (sensor_id) DO UPDATE SET location = %s RETURNING *",
                (sensor_id, location, location)
            )
            result = cur.fetchone()
            conn.commit()

            temperature = round(random.uniform(15.0, 30.0), 1)
            return SensorResponse(
                sensor_id=result["sensor_id"],
                location=result["location"],
                temperature=temperature
            )
    finally:
        conn.close()

@app.get("/sensors", response_model=list[SensorResponse])
def get_all_sensors():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM sensors")
            sensors = cur.fetchall()
            return [
                SensorResponse(
                    sensor_id=sensor["sensor_id"],
                    location=sensor["location"],
                    temperature=round(random.uniform(15.0, 30.0), 1)
                ) for sensor in sensors
            ]
    finally:
        conn.close()

@app.get("/temperature")
def get_temperature(location: str = "", sensor_id: str = ""):
    # If no location is provided, use a default based on sensor ID
    if not location and sensor_id:
        location = SENSOR_TO_LOCATION.get(sensor_id)

    # If no sensor ID is provided, generate one based on location
    if not sensor_id and location:
        sensor_id = LOCATION_TO_SENSOR.get(location)

    if not location and not sensor_id:
        raise HTTPException(status_code=400, detail="Either location or sensor_id must be provided")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if location and not sensor_id:
                # Look up sensor_id by location
                cur.execute("SELECT * FROM sensors WHERE location = %s", (location.strip(),))
                sensor = cur.fetchone()
                if not sensor:
                    # Create a new sensor if location doesn't exist
                    sensor_id = LOCATION_TO_SENSOR.get(location.strip(), generate_unique_sensor_id())
                    cur.execute(
                        "INSERT INTO sensors (sensor_id, location) VALUES (%s, %s) RETURNING *",
                        (sensor_id, location.strip())
                    )
                    sensor = cur.fetchone()
                    conn.commit()
            elif sensor_id and not location:
                # Look up location by sensor_id
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

            return SensorResponse(
                sensor_id=sensor["sensor_id"],
                location=sensor["location"],
                temperature=round(random.uniform(15.0, 30.0), 1)
            )
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
