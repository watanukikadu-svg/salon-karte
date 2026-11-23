// テスト用：Supabase の代わりにブラウザの中だけで動く偽物
(function () {
  const uid = () => crypto.randomUUID();
  const SALON = 's1', ME = 'st1';
  const db = {
    salons: [{ id: SALON, code: 'test', name: 'テストサロン' }],
    staff: [
      { id: ME, salon_id: SALON, user_id: 'u1', login_id: 'owner', display_name: 'ぬき', role: 'owner', is_stylist: true, can_view_sales: true, can_edit_master: true, can_delete_customers: true, can_manage_staff: true, active: true, sort: 0, created_at: '1' },
      { id: 'st2', salon_id: SALON, user_id: 'u2', login_id: 'sato', display_name: '佐藤', role: 'staff', is_stylist: true, can_view_sales: false, can_edit_master: false, can_delete_customers: false, can_manage_staff: false, active: true, sort: 0, created_at: '2' }],
    menus: [['カット', 4800, 60], ['カラー', 7700, 90], ['トリートメント', 4400, 30]].map(([name, price, duration_min], i) => ({ id: 'm' + i, salon_id: SALON, name, price, duration_min, sort: i, active: true, created_at: '' + i })),
    products: [{ id: 'p1', salon_id: SALON, name: 'シャンプー', price: 3300, stock: 10, sort: 0, active: true, created_at: '1' }],
    customers: [{ id: 'c1', salon_id: SALON, name: '佐藤 美咲', kana: 'さとう みさき', tel: '090', birthday: '1992-12-02', hair: '', allergy: 'ジアミン', memo: '', face_path: null }],
    visits: [], visit_menus: [], visit_items: [], visit_photos: [], bookings: [],
  };
  window.__db = db;
  let signedIn = true;
  if (window.__startSignedOut) signedIn = false;
  class Q {
    constructor(t) { this.t = t; this.f = []; this.op = 'select'; this.payload = null; this.ret = false; this.one = null; this.embed = false }
    select(s) { if (this.op === 'select') this.op = 'select'; else this.ret = true; if (s && s.includes('visit_menus')) this.embed = true; return this }
    eq(k, v) { this.f.push(r => r[k] === v); return this } neq(k, v) { this.f.push(r => r[k] !== v); return this }
    in(k, vs) { this.f.push(r => vs.includes(r[k])); return this } order() { return this }
    single() { this.one = 'single'; return this } maybeSingle() { this.one = 'maybe'; return this }
    insert(p) { this.op = 'insert'; this.payload = p; return this } update(p) { this.op = 'update'; this.payload = p; return this } delete() { this.op = 'delete'; return this }
    run() {
      const T = db[this.t]; let out;
      const match = r => this.f.every(f => f(r));
      if (this.op === 'insert') {
        const rows = (Array.isArray(this.payload) ? this.payload : [this.payload]).map(r => ({ id: uid(), created_at: new Date().toISOString(), ...r }));
        rows.forEach(r => { T.push(r); if (this.t === 'visit_items' && r.product_id) { const p = db.products.find(x => x.id === r.product_id); p.stock -= r.qty } });
        if (this.t === 'visit_photos') { const n = db.visit_photos.filter(p => p.visit_id === rows[0].visit_id).length; if (n > 10) return { data: null, error: { message: 'photo limit 10' } } }
        out = rows;
      } else if (this.op === 'update') { out = T.filter(match); out.forEach(r => Object.assign(r, this.payload)) }
      else if (this.op === 'delete') {
        out = T.filter(match);
        out.forEach(r => { if (this.t === 'visit_items' && r.product_id) db.products.find(x => x.id === r.product_id).stock += r.qty });
        db[this.t] = T.filter(r => !match(r));
        if (this.t === 'visits') ['visit_menus', 'visit_items', 'visit_photos'].forEach(k => db[k] = db[k].filter(x => !out.some(v => v.id === x.visit_id)));
        if (this.t === 'customers') db.visits = db.visits.filter(v => !out.some(c => c.id === v.customer_id));
      } else out = T.filter(match);
      out = JSON.parse(JSON.stringify(out));
      if (this.embed) out.forEach(v => ['visit_menus', 'visit_items', 'visit_photos'].forEach(k => v[k] = JSON.parse(JSON.stringify(db[k].filter(x => x.visit_id === v.id)))));
      if (this.one) { if (this.one === 'single' && out.length !== 1) return { data: null, error: { message: 'not single' } }; return { data: out[0] || null, error: null } }
      return { data: (this.op === 'select' || this.ret) ? out : null, error: null };
    }
    then(res, rej) { return Promise.resolve(this.run()).then(res, rej) }
  }
  const listeners = [];
  window.supabase = {
    createClient: () => ({
      from: t => new Q(t),
      auth: {
        getUser: async () => ({ data: { user: signedIn ? { id: window.__uid || 'u1' } : null } }),
        getSession: async () => ({ data: { session: signedIn ? { access_token: 'x' } : null } }),
        signInWithPassword: async ({ email, password }) => { window.__lastEmail = email; if (password === 'password1') { signedIn = true; return { error: null } } return { error: { message: 'bad' } } },
        signOut: async () => { signedIn = false; listeners.forEach(f => f('SIGNED_OUT')); return {} },
        onAuthStateChange: f => listeners.push(f),
        updateUser: async () => ({ error: null }),
      },
      storage: { from: () => ({ upload: async (p) => { window.__uploads = (window.__uploads || []).concat(p); return { error: null } }, remove: async (ps) => { window.__removed = (window.__removed || []).concat(ps); return {} }, createSignedUrls: async (ps) => ({ data: ps.map(p => ({ path: p, signedUrl: 'data:image/gif;base64,R0lGODlhAQABAAAAACw=' })) }) }) },
    }),
  };
})();
