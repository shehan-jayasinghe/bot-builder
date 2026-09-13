import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const templatePath = join(root, "wrangler.template.jsonc");
const wranglerPath = join(root, "wrangler.jsonc");

const requiredForDeploy = [
  "CLOUDFLARE_D1_DATABASE_ID",
  "CLOUDFLARE_D1_DATABASE_NAME",
  "CLOUDFLARE_R2_BUCKET_NAME",
  "CLOUDFLARE_VECTORIZE_INDEX",
];

const values = {
  __CLOUDFLARE_D1_DATABASE_ID__:
    process.env.CLOUDFLARE_D1_DATABASE_ID ?? "local-dev",
  __CLOUDFLARE_D1_DATABASE_NAME__:
    process.env.CLOUDFLARE_D1_DATABASE_NAME ?? "bot-builder",
  __CLOUDFLARE_R2_BUCKET_NAME__:
    process.env.CLOUDFLARE_R2_BUCKET_NAME ?? "bot-builder-kb",
  __CLOUDFLARE_VECTORIZE_INDEX__:
    process.env.CLOUDFLARE_VECTORIZE_INDEX ?? "bot-builder-kb",
};

const strict = process.argv.includes("--strict");
if (strict) {
  const missing = requiredForDeploy.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    console.error(
      `Missing required env vars for deploy: ${missing.join(", ")}`,
    );
    process.exit(1);
  }
}

let contents = readFileSync(templatePath, "utf8");
for (const [placeholder, value] of Object.entries(values)) {
  if (!contents.includes(placeholder)) {
    console.error(`Placeholder ${placeholder} not found in wrangler.template.jsonc`);
    process.exit(1);
  }
  contents = contents.split(placeholder).join(value);
}

writeFileSync(wranglerPath, contents);
console.log("Generated wrangler.jsonc from template:");
console.log(`  D1 id:     ${values.__CLOUDFLARE_D1_DATABASE_ID__}`);
console.log(`  D1 name:   ${values.__CLOUDFLARE_D1_DATABASE_NAME__}`);
console.log(`  R2:        ${values.__CLOUDFLARE_R2_BUCKET_NAME__}`);
console.log(`  Vectorize: ${values.__CLOUDFLARE_VECTORIZE_INDEX__}`);
