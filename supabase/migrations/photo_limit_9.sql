-- 1回の来店につき写真は9枚まで（3列×3段できれいに並ぶため）。本番に適用済み。
CREATE OR REPLACE FUNCTION private.limit_photos()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
begin
  if (select count(*) from public.visit_photos where visit_id = new.visit_id) >= 9 then
    raise exception 'photo limit 9' using errcode = '23514';
  end if;
  return new;
end $function$;
