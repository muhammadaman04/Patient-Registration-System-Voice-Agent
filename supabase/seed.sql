-- =============================================================================
-- Seed: seed.sql
-- Two clearly fictional demo patients for development / review purposes.
-- DO NOT use real patient data.
--
-- Apply AFTER 0001_init.sql:
--   Paste into the Supabase SQL editor and run, OR
--   supabase db push  (will run migrations first, then seeds)
-- =============================================================================

insert into patients (
    first_name, last_name, date_of_birth, sex,
    phone_number, email,
    address_line_1, city, state, zip_code,
    insurance_provider, insurance_member_id,
    preferred_language,
    emergency_contact_name, emergency_contact_phone
) values
(
    'Jane',  'Doe',  '1990-03-15', 'Female',
    '5550001234', 'jane.doe@example.com',
    '123 Maple Street', 'Springfield', 'IL', '62701',
    'Blue Shield', 'BS-000111',
    'English',
    'John Doe', '5550005678'
),
(
    'Carlos', 'Rivera', '1978-11-28', 'Male',
    '5559876543', 'carlos.rivera@example.com',
    '456 Oak Avenue', 'Austin', 'TX', '73301',
    null, null,
    'Spanish',
    null, null
);
