-- 予約なしで来店した人の施術記録から、自動で作った予約（振り返り用）。本番に適用済み。
alter table public.bookings add column if not exists walk_in boolean not null default false;
