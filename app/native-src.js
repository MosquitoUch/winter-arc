// Brücke zwischen der Web-App (index.html) und den nativen Android-Funktionen.
// Wird nur in der Android-App geladen und stellt alles unter window.WAN bereit.
import { Capacitor, CapacitorHttp, registerPlugin } from "@capacitor/core";
import { App } from "@capacitor/app";
import { LocalNotifications } from "@capacitor/local-notifications";
import { KeepAwake } from "@capacitor-community/keep-awake";
import { Health } from "@capgo/capacitor-health";
import { CapacitorUpdater } from "@capgo/capacitor-updater";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

const WidgetBridge = registerPlugin("WidgetBridge");
const REL = "https://github.com/MosquitoUch/winter-arc/releases/download/app-latest/";

// Das Web-Update hat sauber geladen: sonst rollt der Updater auf die letzte gute Version zurück
CapacitorUpdater.notifyAppReady().catch(() => {});

let checking = false;
const updLog = (step, err) => { window.__waUpd = { t: new Date().toLocaleTimeString("de-DE"), step, err: err ? String((err && err.message) || err).slice(0, 200) : "" }; };
async function checkUpdate() {
  if (checking) return { status: "busy" };
  checking = true;
  try {
    updLog("Version prüfen");
    const r = await CapacitorHttp.get({ url: REL + "version.json?t=" + Date.now(), responseType: "json", connectTimeout: 10000, readTimeout: 10000 });
    let v = r.data;
    if (typeof v === "string") { try { v = JSON.parse(v); } catch (e) { v = null; } }
    if (!v || !v.build) { updLog("Version lesen", "Antwort " + r.status + ": " + String(JSON.stringify(r.data)).slice(0, 80)); return { status: "error" }; }
    if (v.build === window.__waBuild) { updLog("aktuell"); return { status: "current", build: v.build }; }
    const nx = await CapacitorUpdater.getNextBundle().catch(() => null);
    if (nx && nx.version === v.build) { updLog("wartet auf Neustart"); return { status: "ready", build: v.build }; }
    updLog("Lade " + v.build);
    const list = await CapacitorUpdater.list().catch(() => ({ bundles: [] }));
    let b = (list.bundles || []).find((x) => x.version === v.build && x.status !== "error");
    if (!b) b = await CapacitorUpdater.download({ url: REL + "www.zip", version: v.build });
    updLog("Vormerken " + v.build);
    await CapacitorUpdater.next({ id: b.id });
    updLog("geladen " + v.build);
    window.dispatchEvent(new CustomEvent("wa-update-ready", { detail: v }));
    return { status: "ready", build: v.build };
  } catch (e) {
    updLog((window.__waUpd && window.__waUpd.step) || "Update", e);
    console.warn("Update-Check", e);
    return { status: "error", err: String((e && e.message) || e) };
  } finally {
    checking = false;
  }
}

async function applyUpdateNow() {
  const n = await CapacitorUpdater.getNextBundle().catch(() => null);
  if (n && n.id) await CapacitorUpdater.set({ id: n.id });
}

// Teilen und Speichern von Dateien (Backup, Lizenz, Zeitraffer): die Web-App nutzt navigator.share,
// das gibt es in der Android-WebView nicht. Also über Dateisystem und das native Teilen-Menü.
const blobToB64 = (blob) => new Promise((res, rej) => {
  const r = new FileReader();
  r.onload = () => res(String(r.result).split(",")[1] || "");
  r.onerror = () => rej(r.error);
  r.readAsDataURL(blob);
});
navigator.canShare = (d) => !!d;
navigator.share = async (d) => {
  d = d || {};
  const files = [];
  for (const f of d.files || []) {
    const name = (f.name || "datei").replace(/[^\w.\-]+/g, "_");
    const w = await Filesystem.writeFile({ path: name, data: await blobToB64(f), directory: Directory.Cache });
    files.push(w.uri);
  }
  try {
    await Share.share({ title: d.title, text: d.text, url: d.url, files: files.length ? files : undefined, dialogTitle: d.title || "Teilen" });
  } catch (e) {
    if (/cancel/i.test(String((e && e.message) || e))) throw new DOMException("Abgebrochen", "AbortError");
    throw e;
  }
};

window.WAN = { Filesystem, Directory, Share, Capacitor, CapacitorHttp, App, LocalNotifications, KeepAwake, Health, CapacitorUpdater, WidgetBridge, checkUpdate, applyUpdateNow, build: __WA_BUILD__ };
window.dispatchEvent(new Event("wan-ready"));
