-- Create the database if it doesn't exist
CREATE DATABASE smarthome;

-- Connect to the database
\c smarthome;

-- Create the sensors table
CREATE TABLE IF NOT EXISTS sensors (
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

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sensors_sensor_id ON sensors(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(type);
CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors(location);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);

-- Insert predefined sensors for mappings
INSERT INTO sensors (sensor_id, name, type, location, unit, status)
VALUES
    ('1', 'Living Room Sensor', 'temperature', 'Living Room', 'Celsius', 'active'),
    ('2', 'Bedroom Sensor', 'temperature', 'Bedroom', 'Celsius', 'active'),
    ('3', 'Kitchen Sensor', 'temperature', 'Kitchen', 'Celsius', 'active')
ON CONFLICT (sensor_id) DO NOTHING;
