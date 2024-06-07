import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const frontendRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendRoot, "../..");
const versionFile = path.join(repoRoot, "VERSION");
const packageJsonFile = path.join(frontendRoot, "package.json");
const packageLockFile = path.join(frontendRoot, "package-lock.json");

function normalizeVersion(raw) {
  const text = String(raw || "").trim();
  return text.replace(/^[vV]/, "");
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf-8"));
}

function writeJson(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, "utf-8");
}

const version = normalizeVersion(fs.readFileSync(versionFile, "utf-8"));
if (!version) {
  throw new Error("VERSION 文件为空，无法同步前端版本。");
}

let changed = false;

const pkg = readJson(packageJsonFile);
if (pkg.version !== version) {
  pkg.version = version;
  writeJson(packageJsonFile, pkg);
  changed = true;
}

if (fs.existsSync(packageLockFile)) {
  const lock = readJson(packageLockFile);
  if (lock.version !== version) {
    lock.version = version;
    changed = true;
  }
  if (lock.packages && lock.packages[""] && lock.packages[""].version !== version) {
    lock.packages[""].version = version;
    changed = true;
  }
  if (changed) {
    writeJson(packageLockFile, lock);
  }
}

if (changed) {
  console.log(`[sync-version] frontend version synced to ${version}`);
}
