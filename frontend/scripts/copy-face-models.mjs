// Copy the two face-api models the app uses (face detector + expression classifier,
// ~0.5 MB total) from node_modules into public/, so they are served locally.
// Runs automatically before `npm run dev` and `npm run build`; the copies are git-ignored.
import { copyFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const source = join(root, "node_modules", "@vladmandic", "face-api", "model");
const target = join(root, "public", "models", "face-api");
const wanted = /^(tiny_face_detector|face_expression)_model/;

if (!existsSync(source)) {
  console.error(`face-api models not found at ${source}; run npm install first`);
  process.exit(1);
}
mkdirSync(target, { recursive: true });
const files = readdirSync(source).filter((name) => wanted.test(name));
for (const name of files) copyFileSync(join(source, name), join(target, name));
console.log(`copied ${files.length} face-api model files to public/models/face-api`);
