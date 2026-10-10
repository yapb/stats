// Emit one static HTML shell per addon/mod route plus a 404 fallback,
// so every view has a clean shareable URL (data loads client-side as usual).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(web, 'dist');
const shell = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(web, 'data', 'latest.json'), 'utf8'));

let made = 0;
function emit(rel) {
  const dir = path.join(dist, rel);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), shell);
  made += 1;
}

for (const a of data.addons || []) {
  if (a.name) {
    emit(path.join('addon', a.name));
  }
}
for (const m of data.mods || []) {
  if (m.gamedir) {
    emit(path.join('mod', m.gamedir));
  }
}
for (const c of data.countries || []) {
  if (c.cc) {
    emit(path.join('country', c.cc));
  }
}
fs.copyFileSync(path.join(dist, 'index.html'), path.join(dist, '404.html'));
console.log('prerendered ' + made + ' routes plus 404 fallback');
