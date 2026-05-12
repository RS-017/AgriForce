-- ============================================================
--  AgriForce Database Schema
--  PostgreSQL 14+
--  Run this in pgAdmin Query Tool against the 'agriforce' DB
-- ============================================================

-- ── Enable UUID extension ────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
--  ENUM TYPES
-- ============================================================

CREATE TYPE user_role AS ENUM (
    'FARMER',
    'WORKER',
    'EQUIPMENT_PROVIDER',
    'ADMIN'
);

CREATE TYPE land_type AS ENUM (
    'IRRIGATED',
    'RAINFED',
    'DRY'
);

CREATE TYPE availability_status AS ENUM (
    'AVAILABLE',
    'BUSY',
    'MIGRATED'
);

CREATE TYPE job_status AS ENUM (
    'OPEN',
    'CLOSED',
    'FILLED'
);

CREATE TYPE application_status AS ENUM (
    'PENDING',
    'ACCEPTED',
    'REJECTED'
);

CREATE TYPE equipment_status AS ENUM (
    'AVAILABLE',
    'BOOKED',
    'MAINTENANCE'
);

CREATE TYPE booking_status AS ENUM (
    'PENDING',
    'CONFIRMED',
    'CANCELLED'
);

CREATE TYPE notification_type AS ENUM (
    'JOB_ALERT',
    'APPLICATION_UPDATE',
    'SUBSIDY_ALERT',
    'SYSTEM'
);

CREATE TYPE season AS ENUM (
    'KHARIF',
    'RABI',
    'ZAID'
);

-- ============================================================
--  LOCATIONS
-- ============================================================

CREATE TABLE states (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE districts (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name     VARCHAR(100) NOT NULL,
    state_id UUID NOT NULL REFERENCES states(id) ON DELETE CASCADE
);

CREATE INDEX idx_districts_state_id ON districts(state_id);

CREATE TABLE taluks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX idx_taluks_district_id ON taluks(district_id);

-- ============================================================
--  CROPS
-- ============================================================

CREATE TABLE crops (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(100) NOT NULL UNIQUE,
    peak_sowing_start   DATE,
    peak_sowing_end     DATE,
    peak_harvest_start  DATE,
    peak_harvest_end    DATE,
    season              season
);

-- ============================================================
--  USERS & PROFILES
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(15)  NOT NULL UNIQUE,
    email           VARCHAR(255) UNIQUE,
    hashed_password TEXT         NOT NULL,
    role            user_role    NOT NULL,
    is_verified     BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role  ON users(role);

CREATE TABLE farmer_profiles (
    id           UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID      NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    farm_size    FLOAT,
    primary_crop VARCHAR(100),
    district     VARCHAR(100),
    taluk        VARCHAR(100),
    land_type    land_type
);

CREATE INDEX idx_farmer_profiles_user_id  ON farmer_profiles(user_id);
CREATE INDEX idx_farmer_profiles_district ON farmer_profiles(district);

CREATE TABLE worker_profiles (
    id                  UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID                NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    experience_years    INTEGER             NOT NULL DEFAULT 0,
    daily_wage          FLOAT               NOT NULL DEFAULT 0.0,
    availability_status availability_status NOT NULL DEFAULT 'AVAILABLE',
    is_migrant          BOOLEAN             NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_worker_profiles_user_id ON worker_profiles(user_id);
CREATE INDEX idx_worker_profiles_availability ON worker_profiles(availability_status);

CREATE TABLE skills (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE worker_skills (
    worker_id UUID NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    skill_id  UUID NOT NULL REFERENCES skills(id)          ON DELETE CASCADE,
    PRIMARY KEY (worker_id, skill_id)
);

-- ============================================================
--  JOBS & APPLICATIONS
-- ============================================================

CREATE TABLE job_posts (
    id                 UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id          UUID       NOT NULL REFERENCES farmer_profiles(id) ON DELETE CASCADE,
    crop_type_id       UUID       NOT NULL REFERENCES crops(id),
    district           VARCHAR(100) NOT NULL,
    taluk              VARCHAR(100),
    workers_required   INTEGER    NOT NULL,
    start_date         DATE       NOT NULL,
    end_date           DATE       NOT NULL,
    daily_wage_offered FLOAT      NOT NULL,
    status             job_status NOT NULL DEFAULT 'OPEN',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_posts_farmer_id    ON job_posts(farmer_id);
CREATE INDEX idx_job_posts_status       ON job_posts(status);
CREATE INDEX idx_job_posts_district     ON job_posts(district);
CREATE INDEX idx_job_posts_created_at   ON job_posts(created_at DESC);

CREATE TABLE applications (
    id         UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id     UUID               NOT NULL REFERENCES job_posts(id)       ON DELETE CASCADE,
    worker_id  UUID               NOT NULL REFERENCES worker_profiles(id) ON DELETE CASCADE,
    status     application_status NOT NULL DEFAULT 'PENDING',
    applied_at TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_application UNIQUE (job_id, worker_id)
);

CREATE INDEX idx_applications_job_id    ON applications(job_id);
CREATE INDEX idx_applications_worker_id ON applications(worker_id);
CREATE INDEX idx_applications_status    ON applications(status);

-- ============================================================
--  EQUIPMENT & RENTAL BOOKINGS
-- ============================================================

CREATE TABLE equipment (
    id                  UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id         UUID             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(200)     NOT NULL,
    type                VARCHAR(100)     NOT NULL,
    description         TEXT,
    daily_rate          FLOAT            NOT NULL,
    district            VARCHAR(100)     NOT NULL,
    availability_status equipment_status NOT NULL DEFAULT 'AVAILABLE',
    images              TEXT[]           NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_equipment_provider_id   ON equipment(provider_id);
CREATE INDEX idx_equipment_district      ON equipment(district);
CREATE INDEX idx_equipment_type          ON equipment(type);
CREATE INDEX idx_equipment_availability  ON equipment(availability_status);

CREATE TABLE rental_bookings (
    id           UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID           NOT NULL REFERENCES equipment(id)        ON DELETE CASCADE,
    farmer_id    UUID           NOT NULL REFERENCES farmer_profiles(id)  ON DELETE CASCADE,
    start_date   DATE           NOT NULL,
    end_date     DATE           NOT NULL,
    total_cost   FLOAT          NOT NULL,
    status       booking_status NOT NULL DEFAULT 'PENDING',
    created_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_booking_dates CHECK (end_date > start_date)
);

CREATE INDEX idx_rental_bookings_equipment_id ON rental_bookings(equipment_id);
CREATE INDEX idx_rental_bookings_farmer_id    ON rental_bookings(farmer_id);
CREATE INDEX idx_rental_bookings_dates        ON rental_bookings(start_date, end_date);

-- ============================================================
--  SUBSIDIES
-- ============================================================

CREATE TABLE subsidy_schemes (
    id                     UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    name                   VARCHAR(255) NOT NULL,
    ministry               VARCHAR(200),
    eligible_land_size_max FLOAT,
    eligible_regions       TEXT[]  NOT NULL DEFAULT '{}',
    deadline               DATE,
    portal_url             TEXT,
    description            TEXT
);

CREATE INDEX idx_subsidy_schemes_deadline ON subsidy_schemes(deadline);

CREATE TABLE subsidy_crop_links (
    scheme_id UUID NOT NULL REFERENCES subsidy_schemes(id) ON DELETE CASCADE,
    crop_id   UUID NOT NULL REFERENCES crops(id)           ON DELETE CASCADE,
    PRIMARY KEY (scheme_id, crop_id)
);

CREATE TABLE eligibility_checks (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id   UUID    NOT NULL REFERENCES farmer_profiles(id)  ON DELETE CASCADE,
    scheme_id   UUID    NOT NULL REFERENCES subsidy_schemes(id)  ON DELETE CASCADE,
    is_eligible BOOLEAN NOT NULL,
    checked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eligibility_checks_farmer_id ON eligibility_checks(farmer_id);
CREATE INDEX idx_eligibility_checks_scheme_id ON eligibility_checks(scheme_id);

-- ============================================================
--  FORECAST
-- ============================================================

CREATE TABLE labour_demand_forecasts (
    id                     UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    district               VARCHAR(100) NOT NULL,
    crop_type_id           UUID         NOT NULL REFERENCES crops(id),
    forecast_date          DATE         NOT NULL,
    predicted_demand_score FLOAT        NOT NULL,
    confidence_lower_80    FLOAT,
    confidence_upper_80    FLOAT,
    confidence_lower_95    FLOAT,
    confidence_upper_95    FLOAT,
    model_version          VARCHAR(50),
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_forecast_district      ON labour_demand_forecasts(district);
CREATE INDEX idx_forecast_date          ON labour_demand_forecasts(forecast_date);
CREATE INDEX idx_forecast_crop_type_id  ON labour_demand_forecasts(crop_type_id);

-- ============================================================
--  NOTIFICATIONS
-- ============================================================

CREATE TABLE notifications (
    id         UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID              NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT              NOT NULL,
    type       notification_type NOT NULL,
    is_read    BOOLEAN           NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id  ON notifications(user_id);
CREATE INDEX idx_notifications_is_read  ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created  ON notifications(created_at DESC);

-- ============================================================
--  SEED DATA — Locations (Major Indian States + Districts)
-- ============================================================

INSERT INTO states (id, name) VALUES
    (gen_random_uuid(), 'Punjab'),
    (gen_random_uuid(), 'Haryana'),
    (gen_random_uuid(), 'Uttar Pradesh'),
    (gen_random_uuid(), 'Maharashtra'),
    (gen_random_uuid(), 'Karnataka'),
    (gen_random_uuid(), 'Tamil Nadu'),
    (gen_random_uuid(), 'Andhra Pradesh'),
    (gen_random_uuid(), 'Madhya Pradesh'),
    (gen_random_uuid(), 'Rajasthan'),
    (gen_random_uuid(), 'Gujarat');

-- Punjab Districts
INSERT INTO districts (id, name, state_id) VALUES
    (gen_random_uuid(), 'Amritsar',  (SELECT id FROM states WHERE name='Punjab')),
    (gen_random_uuid(), 'Ludhiana',  (SELECT id FROM states WHERE name='Punjab')),
    (gen_random_uuid(), 'Jalandhar', (SELECT id FROM states WHERE name='Punjab')),
    (gen_random_uuid(), 'Patiala',   (SELECT id FROM states WHERE name='Punjab')),
    (gen_random_uuid(), 'Bathinda',  (SELECT id FROM states WHERE name='Punjab'));

-- Haryana Districts
INSERT INTO districts (id, name, state_id) VALUES
    (gen_random_uuid(), 'Karnal',   (SELECT id FROM states WHERE name='Haryana')),
    (gen_random_uuid(), 'Hisar',    (SELECT id FROM states WHERE name='Haryana')),
    (gen_random_uuid(), 'Rohtak',   (SELECT id FROM states WHERE name='Haryana')),
    (gen_random_uuid(), 'Panipat',  (SELECT id FROM states WHERE name='Haryana')),
    (gen_random_uuid(), 'Sirsa',    (SELECT id FROM states WHERE name='Haryana'));

-- Maharashtra Districts
INSERT INTO districts (id, name, state_id) VALUES
    (gen_random_uuid(), 'Pune',        (SELECT id FROM states WHERE name='Maharashtra')),
    (gen_random_uuid(), 'Nashik',      (SELECT id FROM states WHERE name='Maharashtra')),
    (gen_random_uuid(), 'Aurangabad',  (SELECT id FROM states WHERE name='Maharashtra')),
    (gen_random_uuid(), 'Nagpur',      (SELECT id FROM states WHERE name='Maharashtra')),
    (gen_random_uuid(), 'Solapur',     (SELECT id FROM states WHERE name='Maharashtra'));

-- Taluks for Amritsar
INSERT INTO taluks (id, name, district_id) VALUES
    (gen_random_uuid(), 'Ajnala',      (SELECT id FROM districts WHERE name='Amritsar')),
    (gen_random_uuid(), 'Baba Bakala', (SELECT id FROM districts WHERE name='Amritsar')),
    (gen_random_uuid(), 'Majitha',     (SELECT id FROM districts WHERE name='Amritsar')),
    (gen_random_uuid(), 'Tarn Taran',  (SELECT id FROM districts WHERE name='Amritsar'));

-- Taluks for Ludhiana
INSERT INTO taluks (id, name, district_id) VALUES
    (gen_random_uuid(), 'Khanna',    (SELECT id FROM districts WHERE name='Ludhiana')),
    (gen_random_uuid(), 'Samrala',   (SELECT id FROM districts WHERE name='Ludhiana')),
    (gen_random_uuid(), 'Jagraon',   (SELECT id FROM districts WHERE name='Ludhiana')),
    (gen_random_uuid(), 'Dehlon',    (SELECT id FROM districts WHERE name='Ludhiana'));

-- ============================================================
--  SEED DATA — Crops with Peak Season Dates
-- ============================================================

INSERT INTO crops (id, name, peak_sowing_start, peak_sowing_end, peak_harvest_start, peak_harvest_end, season) VALUES
    (gen_random_uuid(), 'Wheat',     '2025-11-01', '2025-11-30', '2026-03-15', '2026-04-15', 'RABI'),
    (gen_random_uuid(), 'Rice',      '2025-06-15', '2025-07-15', '2025-10-01', '2025-11-15', 'KHARIF'),
    (gen_random_uuid(), 'Cotton',    '2025-05-01', '2025-06-15', '2025-10-01', '2025-12-31', 'KHARIF'),
    (gen_random_uuid(), 'Sugarcane', '2025-02-01', '2025-03-31', '2025-11-01', '2026-03-31', 'ZAID'),
    (gen_random_uuid(), 'Maize',     '2025-06-01', '2025-07-15', '2025-09-15', '2025-10-31', 'KHARIF'),
    (gen_random_uuid(), 'Soybean',   '2025-06-15', '2025-07-31', '2025-10-01', '2025-11-15', 'KHARIF'),
    (gen_random_uuid(), 'Mustard',   '2025-10-01', '2025-10-31', '2026-02-15', '2026-03-15', 'RABI'),
    (gen_random_uuid(), 'Groundnut', '2025-06-01', '2025-07-15', '2025-09-15', '2025-11-01', 'KHARIF'),
    (gen_random_uuid(), 'Tomato',    '2025-06-01', '2025-07-31', '2025-09-01', '2025-12-31', 'KHARIF'),
    (gen_random_uuid(), 'Onion',     '2025-10-15', '2025-11-30', '2026-02-01', '2026-03-31', 'RABI');

-- ============================================================
--  SEED DATA — Common Agricultural Skills
-- ============================================================

INSERT INTO skills (id, name) VALUES
    (gen_random_uuid(), 'Harvesting'),
    (gen_random_uuid(), 'Sowing'),
    (gen_random_uuid(), 'Tractor Driving'),
    (gen_random_uuid(), 'Pesticide Spraying'),
    (gen_random_uuid(), 'Irrigation Management'),
    (gen_random_uuid(), 'Transplanting'),
    (gen_random_uuid(), 'Weeding'),
    (gen_random_uuid(), 'Pruning'),
    (gen_random_uuid(), 'Threshing'),
    (gen_random_uuid(), 'Post-Harvest Processing');

-- ============================================================
--  SEED DATA — Sample Admin User
--  Password: Admin@1234 (bcrypt hash — change before production)
-- ============================================================

INSERT INTO users (id, phone, email, hashed_password, role, is_verified, is_active)
VALUES (
    gen_random_uuid(),
    '+919000000000',
    'admin@agriforce.in',
    '$2b$12$7y7M4T6Xw.GJHIq3RXt4NuL5WZk1Gk2f5OvI8gSTN5PAOqiN3PXKu',
    'ADMIN',
    TRUE,
    TRUE
);

-- ============================================================
--  SEED DATA — Sample Subsidy Schemes
-- ============================================================

INSERT INTO subsidy_schemes (id, name, ministry, eligible_land_size_max, eligible_regions, deadline, portal_url, description)
VALUES
(
    gen_random_uuid(),
    'PM-KISAN Equipment Subsidy',
    'Ministry of Agriculture & Farmers Welfare',
    5.0,
    ARRAY['Punjab', 'Haryana', 'Uttar Pradesh', 'Maharashtra'],
    '2026-11-15',
    'https://pmkisan.gov.in',
    'Up to 50% subsidy on purchasing new tractors and harvesters for small and marginal farmers with landholding up to 5 acres.'
),
(
    gen_random_uuid(),
    'PMFBY Crop Insurance',
    'Ministry of Agriculture & Farmers Welfare',
    NULL,
    ARRAY['Punjab', 'Haryana', 'Maharashtra', 'Karnataka', 'Tamil Nadu'],
    '2026-07-31',
    'https://pmfby.gov.in',
    'Pradhan Mantri Fasal Bima Yojana provides financial support to farmers suffering crop loss/damage due to unforeseen events.'
),
(
    gen_random_uuid(),
    'RKVY Agricultural Mechanisation',
    'Ministry of Agriculture & Farmers Welfare',
    10.0,
    ARRAY['Uttar Pradesh', 'Madhya Pradesh', 'Rajasthan', 'Gujarat'],
    '2026-09-30',
    'https://rkvy.nic.in',
    'Rashtriya Krishi Vikas Yojana provides 40–50% subsidy on farm mechanisation equipment for registered farmers.'
);

-- ============================================================
--  USEFUL VIEWS
-- ============================================================

-- Active open jobs with crop name
CREATE VIEW v_open_jobs AS
SELECT
    jp.id,
    jp.district,
    jp.taluk,
    c.name            AS crop_name,
    jp.workers_required,
    jp.start_date,
    jp.end_date,
    jp.daily_wage_offered,
    jp.status,
    jp.created_at
FROM job_posts jp
JOIN crops c ON c.id = jp.crop_type_id
WHERE jp.status = 'OPEN';

-- Worker profile with skills array
CREATE VIEW v_worker_summary AS
SELECT
    wp.id,
    u.phone,
    u.email,
    wp.experience_years,
    wp.daily_wage,
    wp.availability_status,
    wp.is_migrant,
    ARRAY_AGG(s.name) FILTER (WHERE s.name IS NOT NULL) AS skills
FROM worker_profiles wp
JOIN users u ON u.id = wp.user_id
LEFT JOIN worker_skills ws ON ws.worker_id = wp.id
LEFT JOIN skills s         ON s.id = ws.skill_id
GROUP BY wp.id, u.phone, u.email;

-- Unread notification count per user
CREATE VIEW v_unread_notifications AS
SELECT
    user_id,
    COUNT(*) AS unread_count
FROM notifications
WHERE is_read = FALSE
GROUP BY user_id;
