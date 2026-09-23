-- Popote — schéma Supabase (même projet que Pages contre minutes, même propriétaire : app_config.owner et is_owner()).
-- À coller tel quel dans Supabase > SQL Editor > Run. Ré-exécutable sans perte de données.

-- Un magasin de documents JSON, une ligne par document : coll ∈ config, aliments, recettes, semaines.
create table if not exists popote_docs (
  coll        text not null,
  id          text not null,
  data        jsonb not null,
  updated_at  timestamptz not null default now(),
  primary key (coll, id)
);
create index if not exists popote_docs_updated_idx on popote_docs (updated_at);

-- Le secret que Claude Code utilise pour lire et écrire les documents (composer la semaine) sans session navigateur.
create table if not exists popote_secret (
  id      int primary key default 1 check (id = 1),
  secret  text not null default replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '')
);
insert into popote_secret (id) values (1) on conflict do nothing;

alter table popote_docs   enable row level security;
alter table popote_secret enable row level security;
drop policy if exists popote_owner_all  on popote_docs;
drop policy if exists popote_owner_read on popote_secret;
create policy popote_owner_all  on popote_docs   for all    to authenticated using (is_owner()) with check (is_owner());
create policy popote_owner_read on popote_secret for select to authenticated using (is_owner());

-- Accès par secret (Claude Code, raccourcis) : tout lire, écrire une liste de documents, en supprimer.
create or replace function popote_dump(p_secret text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if p_secret is null or p_secret <> (select secret from popote_secret where id = 1) then raise exception 'interdit'; end if;
  return coalesce((select jsonb_agg(jsonb_build_object('coll', coll, 'id', id, 'data', data, 'updated_at', updated_at)) from popote_docs), '[]'::jsonb);
end $$;

create or replace function popote_put(p_secret text, p_docs jsonb) returns int
language plpgsql security definer set search_path = public as $$
declare d jsonb; n int := 0;
begin
  if p_secret is null or p_secret <> (select secret from popote_secret where id = 1) then raise exception 'interdit'; end if;
  for d in select * from jsonb_array_elements(p_docs) loop
    if d->>'coll' is null or d->>'id' is null then continue; end if;
    if d->'data' is null or jsonb_typeof(d->'data') = 'null' then
      delete from popote_docs where coll = d->>'coll' and id = d->>'id';
    else
      insert into popote_docs (coll, id, data, updated_at) values (d->>'coll', d->>'id', d->'data', now())
      on conflict (coll, id) do update set data = excluded.data, updated_at = now();
    end if;
    n := n + 1;
  end loop;
  return n;
end $$;

revoke all on function popote_dump(text), popote_put(text, jsonb) from public;
grant execute on function popote_dump(text), popote_put(text, jsonb) to anon, authenticated;
