-- Anonymous lightweight reactions, not verified people or medical endorsements.
-- Table access is intentionally denied; bounded RPCs expose counts only.
-- Visitor token stays in localStorage. Clearing storage or using another browser permits another reaction.

create table public.ainet_note_hearts (
 note_id text not null check (length(note_id) between 1 and 100),
 visitor_token uuid not null,
 created_at timestamptz not null default now(),
 primary key(note_id,visitor_token)
);
alter table public.ainet_note_hearts enable row level security;
revoke all on public.ainet_note_hearts from public, anon, authenticated;
create function public.ainet_heart_counts() returns table(note_id text, hearts bigint)
language sql security definer set search_path='' as $$
 select h.note_id,count(*) from public.ainet_note_hearts h group by h.note_id
$$;
create function public.ainet_set_heart(p_note_id text,p_visitor_token uuid,p_liked boolean)
returns bigint language plpgsql security definer set search_path='' as $$
declare total bigint;
begin
 if p_visitor_token is null or p_liked is null then raise exception 'Invalid request'; end if;
 if p_note_id not in ('seed-gemini','seed-chatgpt') and not exists (
 select 1 from public.instrument_news_comments c where 'note-'||c.id::text=p_note_id
 and c.site='ainet' and c.post_id='love-my-ai-wall' and c.status='approved'
 ) then raise exception 'Unknown note'; end if;
 if p_liked then
 insert into public.ainet_note_hearts(note_id,visitor_token) values(p_note_id,p_visitor_token) on conflict do nothing;
 else
 delete from public.ainet_note_hearts where note_id=p_note_id and visitor_token=p_visitor_token;
 end if;
 select count(*) into total from public.ainet_note_hearts where note_id=p_note_id;
 return total;
end $$;
revoke all on function public.ainet_heart_counts() from public;
revoke all on function public.ainet_set_heart(text,uuid,boolean) from public;
grant execute on function public.ainet_heart_counts() to anon,authenticated;
grant execute on function public.ainet_set_heart(text,uuid,boolean) to anon,authenticated;
