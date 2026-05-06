#!/usr/bin/env node
/**
 * Initialize Constitution Script
 * Checks docs/ for constitution document set (5 files).
 * For any missing file, copies the corresponding template from
 * templates/constitution/{TYPE}.md to docs/ (overwrite: false).
 * Replaces [PROJECT_NAME] placeholders with the project directory name.
 */
const fs = require("fs");
const path = require("path");
const { existsSync, getRepoRoot } = require("./common");

const repoRoot = getRepoRoot();
const docsDir = path.join(repoRoot, "docs");
const templateDir = path.join(
    repoRoot, ".ttadk", "plugins", "ttadk", "core",
    "resources", "templates"
);

const CONSTITUTION_FILES = [
    "CONSTITUTION.md",
    "QUALITY.md",
    "RELIABILITY.md",
    "SECURITY.md",
    "CODING.md",
];

// Template file names follow: constitution/{TYPE}.md
const TEMPLATE_MAP = {
    "CONSTITUTION.md": "constitution/CONSTITUTION.md",
    "QUALITY.md": "constitution/QUALITY.md",
    "RELIABILITY.md": "constitution/RELIABILITY.md",
    "SECURITY.md": "constitution/SECURITY.md",
    "CODING.md": "constitution/CODING.md",
};

// Detect project name from directory name
const projectName = path.basename(repoRoot);

// Check for legacy .ttadk/memory/constitution.md
const legacyPath = path.join(repoRoot, ".ttadk", "memory", "constitution.md");
const hasLegacy = existsSync(legacyPath);

// Ensure docs directory exists
if (!existsSync(docsDir)) {
    fs.mkdirSync(docsDir, { recursive: true });
}

const results = [];

for (const file of CONSTITUTION_FILES) {
    const targetPath = path.join(docsDir, file);
    const templateFile = TEMPLATE_MAP[file];
    const sourcePath = path.join(templateDir, templateFile || file);

    if (existsSync(targetPath)) {
        results.push({ file, status: "exists", path: targetPath });
        continue;
    }

    if (!existsSync(sourcePath)) {
        results.push({ file, status: "missing_template", path: sourcePath });
        continue;
    }

    // Read template, replace [PROJECT_NAME], write to target
    let content = fs.readFileSync(sourcePath, "utf-8");
    content = content.replace(/\[PROJECT_NAME\]/g, projectName);
    // Replace [DATE] with today's date
    const today = new Date().toISOString().split("T")[0];
    content = content.replace(/\[DATE\]/g, today);

    fs.writeFileSync(targetPath, content, "utf-8");
    results.push({ file, status: "created", path: targetPath });
}

console.log(JSON.stringify({
    status: results.every(r => r.status !== "missing_template") ? "ok" : "partial",
    legacy_detected: hasLegacy,
    legacy_path: hasLegacy ? legacyPath : null,
    files: results,
}));
