-- Aevryn PostgreSQL runtime privilege template.
-- Built by Aetherra Labs.
--
-- Purpose:
--   Provision the production runtime database role with normal product-table
--   access while preserving append-only audit history.
--
-- Safety rules:
--   1. Do not commit rendered copies of this file.
--   2. Replace <runtime_role> only in the reviewed execution copy.
--   3. Do not paste database URLs, passwords, hostnames, or usernames into this file.
--   4. Run only after schema bootstrap/migrations have already been applied.
--   5. Cloud Run must use AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false.
--   6. Verify with aevryn audit-access-report and aevryn audit-access-verify.

BEGIN;

GRANT USAGE ON SCHEMA public TO "<runtime_role>";

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.users,
    public.projects,
    public.stories,
    public.imports,
    public.engine_runs,
    public.background_jobs,
    public.snapshots,
    public.exports,
    public.project_settings
TO "<runtime_role>";

GRANT SELECT, INSERT ON TABLE public.audit_ledger_records TO "<runtime_role>";

REVOKE UPDATE, DELETE, TRUNCATE ON TABLE public.audit_ledger_records FROM "<runtime_role>";

COMMIT;
