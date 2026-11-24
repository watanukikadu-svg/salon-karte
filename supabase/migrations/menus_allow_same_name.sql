-- 同じ名前のメニュー（例：カット4500円とカット4000円）を登録できるようにする。本番に適用済み。
alter table public.menus drop constraint if exists menus_salon_id_name_key;
drop index if exists public.menus_salon_id_name_key;
-- 予約で選んだメニューを、名前ではなくメニューそのもの（id）で覚えておく
alter table public.bookings add column if not exists menu_ids text[] not null default '{}';
