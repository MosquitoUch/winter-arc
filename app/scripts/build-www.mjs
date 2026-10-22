// Baut den Web-Teil der Android-App: index.html und Icons aus dem Repo, dazu native.js mit den Capacitor-Plugins.
import { build } from "esbuild";
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const app = join(here, "..");
const root = join(app, "..");
const www = join(app, "www");
const id = (process.env.BUILD_ID || "local").slice(0, 12);

rmSync(www, { recursive: true, force: true });
mkdirSync(www, { recursive: true });
for (const f of ["manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable.png", "privacy.html", "zxing.min.js"]) {
  try { cpSync(join(root, f), join(www, f)); } catch (e) { console.warn("fehlt:", f); }
}
let html = readFileSync(join(root, "index.html"), "utf8");
if (!html.includes('window.__waBuild = "dev"')) throw new Error("Platzhalter window.__waBuild fehlt in index.html");
html = html.replace('window.__waBuild = "dev"', 'window.__waBuild = "' + id + '"');
writeFileSync(join(www, "index.html"), html);

await build({
  entryPoints: [join(app, "native-src.js")],
  bundle: true,
  format: "iife",
  target: ["chrome100"],
  minify: true,
  outfile: join(www, "native.js"),
  define: { __WA_BUILD__: JSON.stringify(id) }
});
writeFileSync(join(www, "version.json"), JSON.stringify({ build: id, date: new Date().toISOString() }) + "\n");
console.log("www gebaut, Build", id);
