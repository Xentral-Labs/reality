import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

import { invariantTerms, isNonCopyValue, languageEquivalentTerms } from "./i18n-invariants.mjs";

export const languages = ["en", "de", "nl", "es"];
const textProps = new Set([
  "title",
  "description",
  "eyebrow",
  "placeholder",
  "detail",
  "label",
  "aria-label",
]);
const protectedDomainTerms =
  /\b(?:Reality|SourceRecords?|Evidence|Commitments?|Reservations?|Movements?)\b/gu;

function propertyName(node) {
  return ts.isStringLiteral(node) || ts.isIdentifier(node) || ts.isNumericLiteral(node)
    ? node.text
    : null;
}

function literalValue(node) {
  return ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) ? node.text : null;
}

function collectObject(object, target) {
  if (!ts.isObjectLiteralExpression(object)) return;
  for (const property of object.properties) {
    if (!ts.isPropertyAssignment(property)) continue;
    const key = propertyName(property.name);
    const value = literalValue(property.initializer);
    if (key !== null && value !== null) target.set(key, value);
  }
}

export function parseCatalogs(localizationFile) {
  const source = fs.readFileSync(localizationFile, "utf8");
  const ast = ts.createSourceFile(
    localizationFile,
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const catalogs = { de: new Map(), nl: new Map(), es: new Map() };
  function visit(node) {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.name.text === "dictionaries" &&
      ts.isObjectLiteralExpression(node.initializer)
    ) {
      for (const property of node.initializer.properties) {
        if (!ts.isPropertyAssignment(property)) continue;
        const language = propertyName(property.name);
        if (language in catalogs) collectObject(property.initializer, catalogs[language]);
      }
    }
    if (
      ts.isCallExpression(node) &&
      ts.isPropertyAccessExpression(node.expression) &&
      node.expression.expression.getText(ast) === "Object" &&
      node.expression.name.text === "assign"
    ) {
      const [target, additions] = node.arguments;
      if (
        target &&
        ts.isPropertyAccessExpression(target) &&
        target.expression.getText(ast) === "dictionaries" &&
        target.name.text in catalogs
      )
        collectObject(additions, catalogs[target.name.text]);
    }
    ts.forEachChild(node, visit);
  }
  visit(ast);
  return catalogs;
}

export function discoverSourceFiles(sourceRoot) {
  const found = [];
  function walk(directory) {
    for (const entry of fs
      .readdirSync(directory, { withFileTypes: true })
      .sort((a, b) => a.name.localeCompare(b.name))) {
      const candidate = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(candidate);
      else if (
        /\.(?:ts|tsx)$/u.test(entry.name) &&
        entry.name !== "localization.tsx" &&
        !entry.name.includes(".test.")
      )
        found.push(candidate);
    }
  }
  walk(sourceRoot);
  return found;
}

export function collectInterfaceStrings(sourceFiles) {
  const candidates = new Map();
  function insideNamedObject(node, name) {
    for (let current = node.parent; current; current = current.parent) {
      if (
        ts.isPropertyAssignment(current) &&
        propertyName(current.name) === name &&
        ts.isObjectLiteralExpression(current.initializer)
      )
        return true;
      if (ts.isVariableDeclaration(current)) return false;
    }
    return false;
  }
  function isGermanAlternative(node) {
    if (insideNamedObject(node, "de")) return true;
    for (let current = node; current.parent; current = current.parent) {
      if (
        ts.isConditionalExpression(current.parent) &&
        current.parent.whenTrue === current &&
        /(?:===\s*["']de["']|^de$)/u.test(current.parent.condition.getText())
      )
        return true;
    }
    return false;
  }
  function add(value, file, node) {
    const normalized = value.replace(/\s+/gu, " ").trim();
    if (normalized.length < 2 || !/[A-Za-z]/u.test(normalized) || isNonCopyValue(normalized))
      return;
    const line = node.getSourceFile().getLineAndCharacterOfPosition(node.getStart()).line + 1;
    const locations = candidates.get(normalized) || new Set();
    locations.add(`${file}:${line}`);
    candidates.set(normalized, locations);
  }
  for (const file of sourceFiles) {
    const source = fs.readFileSync(file, "utf8");
    const ast = ts.createSourceFile(
      file,
      source,
      ts.ScriptTarget.Latest,
      true,
      file.endsWith("x") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
    );
    function visit(node) {
      if (isGermanAlternative(node)) return;
      if (ts.isJsxText(node)) add(node.text, file, node);
      if (
        ts.isJsxAttribute(node) &&
        textProps.has(node.name.text) &&
        node.initializer &&
        ts.isStringLiteral(node.initializer)
      )
        add(node.initializer.text, file, node);
      if (
        ts.isCallExpression(node) &&
        ts.isIdentifier(node.expression) &&
        node.expression.text === "t" &&
        node.arguments[0]
      ) {
        const value = literalValue(node.arguments[0]);
        if (value !== null) add(value, file, node.arguments[0]);
      }
      if (ts.isStringLiteral(node) && ts.isArrayLiteralExpression(node.parent))
        add(node.text, file, node);
      if (
        (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) &&
        insideNamedObject(node, "en")
      )
        add(node.text, file, node);
      if (
        (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) &&
        ts.isConditionalExpression(node.parent)
      )
        add(node.text, file, node);
      ts.forEachChild(node, visit);
    }
    visit(ast);
  }
  return candidates;
}

export function auditLocalization({ sourceRoot, localizationFile }) {
  const inventory = collectInterfaceStrings(discoverSourceFiles(sourceRoot));
  const catalogs = parseCatalogs(localizationFile);
  return languages.map((language) => {
    const missing = [];
    const invalid = [];
    let invariant = 0;
    for (const [source, locations] of [...inventory.entries()].sort(([a], [b]) =>
      a.localeCompare(b),
    )) {
      if (language === "en") continue;
      if (
        invariantTerms.has(source) ||
        (language !== "en" && languageEquivalentTerms[language].has(source))
      ) {
        invariant += 1;
        continue;
      }
      const value = catalogs[language].get(source);
      if (value === undefined) missing.push({ source, locations: [...locations].sort() });
      else {
        const requiredTerms = source.match(protectedDomainTerms) || [];
        const losesDomainTerm = requiredTerms.some((term) => !value.includes(term));
        if (!value.trim() || value === source || losesDomainTerm)
          invalid.push({ source, locations: [...locations].sort() });
      }
    }
    return {
      language,
      discovered: inventory.size,
      covered:
        language === "en" ? inventory.size : inventory.size - missing.length - invalid.length,
      invariant,
      missing,
      invalid,
      status: missing.length === 0 && invalid.length === 0 ? "pass" : "fail",
    };
  });
}

export function formatResults(results, relativeTo = process.cwd()) {
  const lines = [];
  for (const result of results) {
    lines.push(
      `${result.language}: ${result.status.toUpperCase()} — ${result.covered}/${result.discovered} covered, ${result.invariant} invariant, ${result.missing.length} missing, ${result.invalid.length} invalid`,
    );
    for (const [kind, issue] of [
      ...result.missing.map((item) => ["missing", item]),
      ...result.invalid.map((item) => ["invalid", item]),
    ]) {
      lines.push(`- ${kind}: ${issue.source}`);
      for (const location of issue.locations)
        lines.push(`  at ${path.relative(relativeTo, location)}`);
    }
  }
  return lines.join("\n");
}
