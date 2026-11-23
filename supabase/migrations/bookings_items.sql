-- 予約のときに「店販を買う」と決まっている商品（[{product_id, name, price, qty}]）。本番に適用済み。
alter table public.bookings add column if not exists items jsonb not null default '[]'::jsonb;
