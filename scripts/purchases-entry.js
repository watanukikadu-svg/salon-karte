// iPhone アプリにだけ入れる課金の部品（RevenueCat）。build.mjs が www/purchases.js にまとめる。
// index.html からは window.RCPurchases で使う（Web 版のサイトには入らない）。
import { Purchases } from "@revenuecat/purchases-capacitor";
window.RCPurchases = Purchases;
