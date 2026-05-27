-- seed.sql
TRUNCATE TABLE alert CASCADE;
TRUNCATE TABLE detection_event CASCADE;
TRUNCATE TABLE neighbourhood_join_request CASCADE;
TRUNCATE TABLE camera CASCADE;
TRUNCATE TABLE geospatial_zone CASCADE;
TRUNCATE TABLE retention_policy CASCADE;
TRUNCATE TABLE audit_log CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE property CASCADE;
TRUNCATE TABLE neighbourhood CASCADE;

-- Neighbourhoods
INSERT INTO neighbourhood (id, name, location, join_code, created_at) VALUES
('a1111111-1111-1111-1111-111111111111', 'Northwood Estate', 'Johannesburg North', 'NORTH-5F3A', now()),
('a2222222-2222-2222-2222-222222222222', 'Sunset Valley', 'Cape Town', 'SUNSET-8B2C', now());

-- Users (fixed: first_name/last_name match model)
INSERT INTO users (id, email, first_name, last_name, cognito_sub, role, neighbourhood_id, created_at) VALUES
('b1111111-1111-1111-1111-111111111111', 'admin@northwood.com', 'Sarah', 'Johnson', 'cognito-admin-1', 'NEIGHBOURHOOD_ADMIN', 'a1111111-1111-1111-1111-111111111111', now()),
('b2222222-2222-2222-2222-222222222222', 'admin@sunset.com', 'Mark', 'Williams', 'cognito-admin-2', 'NEIGHBOURHOOD_ADMIN', 'a2222222-2222-2222-2222-222222222222', now()),
('b3333333-3333-3333-3333-333333333333', 'security@northwood.com', 'James', 'Anderson', 'cognito-security-1', 'SECURITY_OFFICER', 'a1111111-1111-1111-1111-111111111111', now()),
('b4444444-4444-4444-4444-444444444444', 'resident1@northwood.com', 'Emily', 'Davis', 'cognito-resident-1', 'RESIDENT', 'a1111111-1111-1111-1111-111111111111', now()),
('b5555555-5555-5555-5555-555555555555', 'resident2@northwood.com', 'Michael', 'Brown', 'cognito-resident-2', 'RESIDENT', 'a1111111-1111-1111-1111-111111111111', now()),
('b6666666-6666-6666-6666-666666666666', 'newuser1@example.com', 'Lisa', 'Martinez', 'cognito-new-1', 'USER', NULL, now()),
('b7777777-7777-7777-7777-777777777777', 'newuser2@example.com', 'David', 'Garcia', 'cognito-new-2', 'USER', NULL, now()),
('b8888888-8888-8888-8888-888888888888', 'newuser3@example.com', 'Jennifer', 'Taylor', 'cognito-new-3', 'USER', NULL, now());

-- Properties (fixed: added property_type)
INSERT INTO property (id, neighbourhood_id, address, property_type, created_at) VALUES
('c1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', '123 Main Street', 'PRIVATE', now()),
('c2222222-2222-2222-2222-222222222222', 'a1111111-1111-1111-1111-111111111111', '456 Oak Avenue', 'PRIVATE', now()),
('c3333333-3333-3333-3333-333333333333', 'a2222222-2222-2222-2222-222222222222', '789 Beach Road', 'PRIVATE', now());

-- Cameras
INSERT INTO camera (id, property_id, neighbourhood_id, visibility, location, rtsp_url, created_at) VALUES
('d1111111-1111-1111-1111-111111111111', 'c1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', 'PUBLIC', 'Front Gate', 'rtsp://camera1.example.com/stream', now()),
('d2222222-2222-2222-2222-222222222222', 'c1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', 'PUBLIC', 'Back Entrance', 'rtsp://camera2.example.com/stream', now()),
('d3333333-3333-3333-3333-333333333333', 'c2222222-2222-2222-2222-222222222222', 'a1111111-1111-1111-1111-111111111111', 'RESTRICTED', 'Side Garage', 'rtsp://camera3.example.com/stream', now());

-- Geospatial Zones (fixed: removed created_at, added required polygon_boundary)
INSERT INTO geospatial_zone (id, neighbourhood_id, name, sensitivity_level, polygon_boundary) VALUES
('e1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', 'Main Entrance Zone', 'HIGH',
 ST_GeomFromText('POLYGON((28.0478 -26.2041, 28.0479 -26.2041, 28.0479 -26.2042, 28.0478 -26.2042, 28.0478 -26.2041))', 4326)),
('e2222222-2222-2222-2222-222222222222', 'a1111111-1111-1111-1111-111111111111', 'Parking Area Zone', 'MEDIUM',
 ST_GeomFromText('POLYGON((28.0480 -26.2043, 28.0481 -26.2043, 28.0481 -26.2044, 28.0480 -26.2044, 28.0480 -26.2043))', 4326));

-- Detection Events (fixed: removed created_at, not in model)
INSERT INTO detection_event (id, camera_id, frame_timestamp, detection_type, confidence_score, thumbnail_url, processed) VALUES
('f1111111-1111-1111-1111-111111111111', 'd1111111-1111-1111-1111-111111111111', now() - interval '5 minutes',  'WEAPON_DETECTED', 0.92, 'https://images.unsplash.com/photo-1557597774-9d273605dfa9?w=800&h=450&fit=crop', true),
('f2222222-2222-2222-2222-222222222222', 'd2222222-2222-2222-2222-222222222222', now() - interval '15 minutes', 'FALL_DETECTED',    0.88, 'https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=800&h=450&fit=crop', true),
('f3333333-3333-3333-3333-333333333333', 'd1111111-1111-1111-1111-111111111111', now() - interval '30 minutes', 'LOITERING',        0.75, 'https://images.unsplash.com/photo-1551958219-acbc608c6377?w=800&h=450&fit=crop', true),
('f4444444-4444-4444-4444-444444444444', 'd3333333-3333-3333-3333-333333333333', now() - interval '1 hour',     'PERIMETER_SCAN',   0.82, 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=800&h=450&fit=crop', true),
('f5555555-5555-5555-5555-555555555555', 'd2222222-2222-2222-2222-222222222222', now() - interval '2 hours',    'HUMAN_PRESENCE',   0.70, 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&h=450&fit=crop', true),
('f6666666-6666-6666-6666-666666666666', 'd1111111-1111-1111-1111-111111111111', now() - interval '3 hours',    'HUMAN_PRESENCE',   0.68, 'https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?w=800&h=450&fit=crop', true);

-- Alerts (fixed: UUIDs use only hex chars 0-9 a-f)
INSERT INTO alert (id, camera_id, detection_event_id, status, resolved_by, resolved_at, created_at) VALUES
('a0111111-1111-1111-1111-111111111111', 'd1111111-1111-1111-1111-111111111111', 'f1111111-1111-1111-1111-111111111111', 'OPEN',         NULL,                                   NULL,                                   now() - interval '5 minutes'),
('a0222222-2222-2222-2222-222222222222', 'd2222222-2222-2222-2222-222222222222', 'f2222222-2222-2222-2222-222222222222', 'OPEN',         NULL,                                   NULL,                                   now() - interval '15 minutes'),
('a0333333-3333-3333-3333-333333333333', 'd1111111-1111-1111-1111-111111111111', 'f3333333-3333-3333-3333-333333333333', 'OPEN',         NULL,                                   NULL,                                   now() - interval '30 minutes'),
('a0444444-4444-4444-4444-444444444444', 'd3333333-3333-3333-3333-333333333333', 'f4444444-4444-4444-4444-444444444444', 'ACKNOWLEDGED', NULL,                                   NULL,                                   now() - interval '1 hour'),
('a0555555-5555-5555-5555-555555555555', 'd2222222-2222-2222-2222-222222222222', 'f5555555-5555-5555-5555-555555555555', 'ACKNOWLEDGED', NULL,                                   NULL,                                   now() - interval '2 hours'),
('a0666666-6666-6666-6666-666666666666', 'd1111111-1111-1111-1111-111111111111', 'f6666666-6666-6666-6666-666666666666', 'RESOLVED',     'b3333333-3333-3333-3333-333333333333', now() - interval '2 hours 30 minutes', now() - interval '3 hours');

-- Join Requests (fixed: UUIDs use only hex chars)
INSERT INTO neighbourhood_join_request (id, neighbourhood_id, user_id, status, created_at, resolved_at) VALUES
('b0111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', 'b6666666-6666-6666-6666-666666666666', 'PENDING',  now() - interval '1 day',    NULL),
('b0222222-2222-2222-2222-222222222222', 'a1111111-1111-1111-1111-111111111111', 'b7777777-7777-7777-7777-777777777777', 'PENDING',  now() - interval '2 hours',  NULL),
('b0333333-3333-3333-3333-333333333333', 'a1111111-1111-1111-1111-111111111111', 'b8888888-8888-8888-8888-888888888888', 'PENDING',  now() - interval '30 minutes', NULL),
('b0444444-4444-4444-4444-444444444444', 'a1111111-1111-1111-1111-111111111111', 'b4444444-4444-4444-4444-444444444444', 'APPROVED', now() - interval '30 days',  now() - interval '29 days'),
('b0555555-5555-5555-5555-555555555555', 'a1111111-1111-1111-1111-111111111111', 'b7777777-7777-7777-7777-777777777777', 'DENIED',   now() - interval '5 days',   now() - interval '4 days');