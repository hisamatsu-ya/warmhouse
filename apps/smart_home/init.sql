-- Create the smarthome database if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smarthome') THEN
        CREATE DATABASE smarthome;
    END IF;
END $$;

-- Connect to the smarthome database
\c smarthome;

-- Create the sensors table if it doesn't exist
CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    value FLOAT DEFAULT 0,
    unit VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries if they don't exist
CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(type);
CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors(location);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);

-- Create the smarthome_py database if it doesn't exist


-- Create the sensors_py table if it doesn't exist !!!
CREATE TABLE IF NOT EXISTS sensors_py (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    value FLOAT DEFAULT 0,
    unit VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries if they don't exist
CREATE INDEX IF NOT EXISTS idx_sensors_py_sensor_id ON sensors_py(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensors_py_type ON sensors_py(type);
CREATE INDEX IF NOT EXISTS idx_sensors_py_location ON sensors_py(location);
CREATE INDEX IF NOT EXISTS idx_sensors_py_status ON sensors_py(status);

-- Insert predefined sensors for mappings
INSERT INTO sensors_py (sensor_id, name, type, location, unit, status)
VALUES
    ('1', 'Living Room Sensor', 'temperature', 'Living Room', 'Celsius', 'active'),
    ('2', 'Bedroom Sensor', 'temperature', 'Bedroom', 'Celsius', 'active'),
    ('3', 'Kitchen Sensor', 'temperature', 'Kitchen', 'Celsius', 'active')
ON CONFLICT (sensor_id) DO NOTHING;
