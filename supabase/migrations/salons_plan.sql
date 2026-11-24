-- 課金（有料プラン）の状態をお店ごとに記録する。
-- 書きかえるのはサーバー（Edge Function salon-admin が RevenueCat に確かめて）だけ。
-- アプリ（オーナー）はお店の名前を変えられるが、この欄は変えられないようにする。
alter table public.salons
  add column if not exists plan_until timestamptz,          -- 有料プランの期限（これより前なら課金中）
  add column if not exists plan_store text,                 -- どこで払ったか（app_store / rc_billing など）
  add column if not exists plan_checked_at timestamptz;     -- サーバーが最後に確かめた時

create or replace function private.salons_keep_plan() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(auth.role(), '') <> 'service_role' and (
       new.plan_until is distinct from old.plan_until
    or new.plan_store is distinct from old.plan_store
    or new.plan_checked_at is distinct from old.plan_checked_at) then
    raise exception 'plan columns are managed by the server';
  end if;
  return new;
end $$;

drop trigger if exists salons_keep_plan on public.salons;
create trigger salons_keep_plan before update on public.salons
  for each row execute function private.salons_keep_plan();
