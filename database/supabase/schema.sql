-- =============================================================================
-- Tunnel Vision – Supabase / PostgreSQL Schema
-- =============================================================================
-- Run this script once against your Supabase project via the SQL editor or
-- the Supabase CLI:  supabase db reset  (for local dev with seed)
-- All statements are idempotent (IF NOT EXISTS / OR REPLACE) so re-running
-- is safe.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. User profiles
--    Extends the built-in auth.users table maintained by Supabase Auth.
--    Created automatically via the trigger below on first sign-up.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
  id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email       TEXT        NOT NULL,
  display_name TEXT,
  avatar_url  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE profiles IS
  'One row per authenticated user, mirroring auth.users with extra app fields.';


-- ---------------------------------------------------------------------------
-- 2. Upload jobs
--    Tracks the status of every data-export file submitted for processing.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upload_jobs (
  id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              UUID        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  filename             TEXT        NOT NULL,
  file_type            TEXT        NOT NULL CHECK (file_type IN ('zip', 'json')),
  status               TEXT        NOT NULL DEFAULT 'queued'
                                   CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
  error_message        TEXT,
  entities_extracted   INTEGER     NOT NULL DEFAULT 0,
  categories_extracted INTEGER     NOT NULL DEFAULT 0,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS upload_jobs_user_id_idx   ON upload_jobs (user_id);
CREATE INDEX IF NOT EXISTS upload_jobs_status_idx    ON upload_jobs (status);
CREATE INDEX IF NOT EXISTS upload_jobs_created_at_idx ON upload_jobs (created_at DESC);

COMMENT ON TABLE upload_jobs IS
  'Processing queue: one row per uploaded file, updated as the pipeline progresses.';
COMMENT ON COLUMN upload_jobs.status IS
  'queued → processing → completed | failed';


-- ---------------------------------------------------------------------------
-- 3. User entity cache
--    Denormalised copy of Neo4j entity data for fast dashboard queries
--    without hitting the graph database on every page load.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_entities (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  entity_name TEXT        NOT NULL,
  entity_type TEXT        NOT NULL,
  weight      FLOAT       NOT NULL DEFAULT 0 CHECK (weight >= 0),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT user_entities_unique UNIQUE (user_id, entity_name)
);

CREATE INDEX IF NOT EXISTS user_entities_user_id_idx ON user_entities (user_id);
CREATE INDEX IF NOT EXISTS user_entities_weight_idx  ON user_entities (user_id, weight DESC);

COMMENT ON TABLE user_entities IS
  'Denormalised cache of the user''s top entities from Neo4j, refreshed after each ingestion job.';


-- ---------------------------------------------------------------------------
-- 4. Row-Level Security
--    Every table uses RLS so the PostgREST auto-API is safe to expose.
--    Supabase Auth populates auth.uid() from the JWT on each request.
-- ---------------------------------------------------------------------------

ALTER TABLE profiles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_jobs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_entities ENABLE ROW LEVEL SECURITY;

-- Profiles: each user can read and update only their own row.
DROP POLICY IF EXISTS "profiles_select_own" ON profiles;
CREATE POLICY "profiles_select_own"
  ON profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_update_own" ON profiles;
CREATE POLICY "profiles_update_own"
  ON profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- Upload jobs: each user manages only their own jobs.
DROP POLICY IF EXISTS "jobs_own" ON upload_jobs;
CREATE POLICY "jobs_own"
  ON upload_jobs FOR ALL USING (auth.uid() = user_id);

-- User entities: each user sees only their own cache.
DROP POLICY IF EXISTS "entities_own" ON user_entities;
CREATE POLICY "entities_own"
  ON user_entities FOR ALL USING (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 5. updated_at auto-timestamp trigger
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  -- profiles
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_profiles_updated_at'
  ) THEN
    CREATE TRIGGER set_profiles_updated_at
      BEFORE UPDATE ON profiles
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- upload_jobs
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_upload_jobs_updated_at'
  ) THEN
    CREATE TRIGGER set_upload_jobs_updated_at
      BEFORE UPDATE ON upload_jobs
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- user_entities
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_entities_updated_at'
  ) THEN
    CREATE TRIGGER set_user_entities_updated_at
      BEFORE UPDATE ON user_entities
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END;
$$;


-- ---------------------------------------------------------------------------
-- 6. Auto-create profile on first sign-up
--    Fires immediately after Supabase Auth inserts the user record.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;   -- idempotent: safe on duplicate auth events
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
