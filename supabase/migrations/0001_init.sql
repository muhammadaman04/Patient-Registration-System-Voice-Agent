-- =============================================================================
-- Migration: 0001_init.sql
-- Creates the `patients` table with all constraints, indexes, and the
-- auto-update trigger for the `updated_at` column.
--
-- Apply via:
--   Supabase SQL editor (paste and run), OR
--   supabase db push  (if using the Supabase CLI with supabase/config.toml)
-- =============================================================================

-- Needed for gen_random_uuid() (already enabled on most Supabase projects)
create extension if not exists pgcrypto;

-- =============================================================================
-- Table
-- =============================================================================

create table if not exists patients (
    patient_id              uuid        primary key default gen_random_uuid(),

    -- Name
    first_name              text        not null
                                        check (char_length(first_name) between 1 and 50),
    last_name               text        not null
                                        check (char_length(last_name)  between 1 and 50),

    -- Demographics
    date_of_birth           date        not null
                                        check (date_of_birth <= current_date),
    sex                     text        not null
                                        check (sex in ('Male', 'Female', 'Other', 'Decline to Answer')),

    -- Contact
    phone_number            text        not null
                                        check (phone_number ~ '^\d{10}$'),
    email                   text
                                        check (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),

    -- Address
    address_line_1          text        not null,
    address_line_2          text,
    city                    text        not null
                                        check (char_length(city) between 1 and 100),
    state                   text        not null
                                        check (char_length(state) = 2),
    zip_code                text        not null
                                        check (zip_code ~ '^\d{5}(-\d{4})?$'),

    -- Insurance (optional)
    insurance_provider      text,
    insurance_member_id     text,

    -- Preferences
    preferred_language      text        not null default 'English',

    -- Emergency contact (optional)
    emergency_contact_name  text,
    emergency_contact_phone text
                                        check (
                                            emergency_contact_phone is null
                                            or emergency_contact_phone ~ '^\d{10}$'
                                        ),

    -- Timestamps
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now(),
    deleted_at              timestamptz                         -- null = active record
);

-- =============================================================================
-- Indexes  (partial — exclude soft-deleted rows for efficiency)
-- =============================================================================

create index if not exists idx_patients_phone
    on patients (phone_number)
    where deleted_at is null;

create index if not exists idx_patients_last_name
    on patients (lower(last_name))
    where deleted_at is null;

-- =============================================================================
-- Trigger: keep updated_at current on every UPDATE
-- =============================================================================

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_patients_updated_at on patients;

create trigger trg_patients_updated_at
before update on patients
for each row execute function set_updated_at();
