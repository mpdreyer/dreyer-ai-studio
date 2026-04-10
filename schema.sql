-- Dreyer AI Studio · Supabase Schema
-- Kör detta i Supabase SQL Editor en gång

-- Projekt
create table if not exists projects (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz default now(),
  name        text not null,
  client      text,
  status      text default 'active',
  current_phase int default 1,
  health_score  int default 75,
  token_budget  float default 20.0,
  token_used    float default 0.0,
  deadline    date,
  deployment_mode text default 'cloud'
);

-- Uppgifter
create table if not exists tasks (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  title       text not null,
  owner_agent text,
  phase       int default 1,
  status      text default 'todo',
  blocks_delivery boolean default false
);

-- Leveranser
create table if not exists deliverables (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  title       text not null,
  owner_agent text,
  doc_type    text,
  status      text default 'pending',
  content     text
);

-- Rådslag-logg
create table if not exists chat_messages (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  role        text not null,
  agent       text,
  model       text,
  content     text not null,
  tokens_used int default 0,
  cost_usd    float default 0.0
);

-- Token-logg per agent
create table if not exists token_log (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  agent       text not null,
  model       text not null,
  tokens_in   int default 0,
  tokens_out  int default 0,
  cost_usd    float default 0.0
);

-- Correction Delta
create table if not exists corrections (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  agent       text not null,
  original    text,
  corrected   text,
  delta_type  text
);

-- Svärm-körningar
create table if not exists swarm_runs (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references projects(id) on delete cascade,
  created_at  timestamptz default now(),
  variant_id  text not null,
  variant     text not null,
  n_workers   int  not null,
  status      text default 'running',
  pass_rate   float,
  median_score float,
  p95_latency  float,
  decision    text
);

create table if not exists worker_results (
  id          uuid primary key default gen_random_uuid(),
  run_id      uuid references swarm_runs(id) on delete cascade,
  worker_idx  int  not null,
  testcase_id text not null,
  score       float,
  latency_ms  int,
  passed      boolean,
  error       text,
  created_at  timestamptz default now()
);

-- Demo-projekt för snabbstart
insert into projects (name, client, current_phase, health_score, token_budget, deadline, deployment_mode)
values ('AI POC', 'Kund X', 3, 74, 20.0, now() + interval '15 days', 'airgap')
on conflict do nothing;
