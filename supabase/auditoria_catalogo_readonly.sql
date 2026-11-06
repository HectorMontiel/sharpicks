-- Catalog audit for an isolated Supabase staging project.
-- Read-only: this file does not read application rows or modify schema/data.
-- Run the complete file in one session; every result is metadata-only.
BEGIN TRANSACTION READ ONLY;

-- Database version and installed extensions. Compare with the project settings.
SELECT current_database() AS database_name,
       current_setting('server_version') AS postgres_version,
       e.extname AS extension_name,
       e.extversion AS extension_version,
       n.nspname AS extension_schema
FROM pg_catalog.pg_extension AS e
JOIN pg_catalog.pg_namespace AS n ON n.oid = e.extnamespace
ORDER BY e.extname;

-- Public tables: RLS, FORCE RLS, policy count and client-role table privileges.
SELECT n.nspname AS schema_name,
       c.relname AS table_name,
       c.relrowsecurity AS rls_enabled,
       c.relforcerowsecurity AS force_rls,
       (SELECT count(*) FROM pg_catalog.pg_policy AS p
        WHERE p.polrelid = c.oid) AS policy_count,
       has_table_privilege('anon', c.oid, 'SELECT') AS anon_select,
       has_table_privilege('anon', c.oid, 'INSERT') AS anon_insert,
       has_table_privilege('anon', c.oid, 'UPDATE') AS anon_update,
       has_table_privilege('anon', c.oid, 'DELETE') AS anon_delete,
       has_table_privilege('authenticated', c.oid, 'SELECT') AS authenticated_select,
       has_table_privilege('authenticated', c.oid, 'INSERT') AS authenticated_insert,
       has_table_privilege('authenticated', c.oid, 'UPDATE') AS authenticated_update,
       has_table_privilege('authenticated', c.oid, 'DELETE') AS authenticated_delete
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind IN ('r', 'p', 'f')
ORDER BY n.nspname, c.relname;

-- Public views/materialized views: owner, security_invoker option and SELECT.
SELECT n.nspname AS schema_name,
       c.relname AS view_name,
       CASE c.relkind WHEN 'm' THEN 'materialized_view' ELSE 'view' END AS object_kind,
       pg_catalog.pg_get_userbyid(c.relowner) AS owner_name,
       COALESCE(bool_or(o.option_name = 'security_invoker'
                        AND o.option_value = 'true'), false) AS security_invoker,
       has_table_privilege('anon', c.oid, 'SELECT') AS anon_select,
       has_table_privilege('authenticated', c.oid, 'SELECT') AS authenticated_select
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
LEFT JOIN LATERAL pg_catalog.pg_options_to_table(c.reloptions) AS o ON true
WHERE n.nspname = 'public'
  AND c.relkind IN ('v', 'm')
GROUP BY n.nspname, c.relname, c.relkind, c.relowner, c.oid
ORDER BY n.nspname, c.relname;

-- Public sequence privileges are independent of table privileges.
SELECT n.nspname AS schema_name,
       c.relname AS sequence_name,
       has_sequence_privilege('anon', c.oid, 'USAGE') AS anon_usage,
       has_sequence_privilege('anon', c.oid, 'SELECT') AS anon_select,
       has_sequence_privilege('anon', c.oid, 'UPDATE') AS anon_update,
       has_sequence_privilege('authenticated', c.oid, 'USAGE') AS authenticated_usage,
       has_sequence_privilege('authenticated', c.oid, 'SELECT') AS authenticated_select,
       has_sequence_privilege('authenticated', c.oid, 'UPDATE') AS authenticated_update
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind = 'S'
ORDER BY n.nspname, c.relname;

-- SECURITY DEFINER routines. Names, identity arguments, search_path and
-- effective EXECUTE flags only; routine bodies and application data are omitted.
SELECT n.nspname AS schema_name,
       p.proname AS routine_name,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments,
       pg_catalog.pg_get_userbyid(p.proowner) AS owner_name,
       p.proconfig AS function_settings,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_execute,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_execute
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.prosecdef
ORDER BY n.nspname, p.proname, identity_arguments;

-- Enabled/non-internal triggers on public tables, with function identity.
SELECT n.nspname AS schema_name,
       c.relname AS table_name,
       t.tgname AS trigger_name,
       t.tgenabled AS enabled_state,
       p.proname AS function_name,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments
FROM pg_catalog.pg_trigger AS t
JOIN pg_catalog.pg_class AS c ON c.oid = t.tgrelid
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
JOIN pg_catalog.pg_proc AS p ON p.oid = t.tgfoid
WHERE n.nspname = 'public'
  AND NOT t.tgisinternal
ORDER BY n.nspname, c.relname, t.tgname;

ROLLBACK;
