#!/usr/bin/env node
/**
 * Copy Quality Linter
 * Grades site copy /20 points with penalties for style issues.
 *
 * Penalties:
 * - Em dash (—): -2 points each
 * - ", not ": -1 point each
 *
 * Fails build if score < 10/20
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, extname } from 'path';

const PENALTIES = {
  EM_DASH: { pattern: /—/g, points: 2, name: 'em dash (—)' },
  NOT_CONSTRUCT: { pattern: /, not /gi, points: 1, name: '", not " construct' },
};

const SCAN_EXTENSIONS = ['.astro', '.md', '.html'];
const SCAN_DIRS = ['src/pages', 'src/layouts'];
const MAX_SCORE = 20;
const MIN_PASSING = 10;

function findFiles(dir, files = []) {
  try {
    const items = readdirSync(dir);
    for (const item of items) {
      const fullPath = join(dir, item);
      const stat = statSync(fullPath);
      if (stat.isDirectory()) {
        findFiles(fullPath, files);
      } else if (SCAN_EXTENSIONS.includes(extname(item))) {
        files.push(fullPath);
      }
    }
  } catch (e) {
    // Directory doesn't exist, skip
  }
  return files;
}

function lintFile(filePath) {
  const content = readFileSync(filePath, 'utf-8');
  const issues = [];

  for (const [key, rule] of Object.entries(PENALTIES)) {
    const matches = content.match(rule.pattern);
    if (matches) {
      for (const match of matches) {
        // Find line number
        const beforeMatch = content.substring(0, content.indexOf(match));
        const lineNum = (beforeMatch.match(/\n/g) || []).length + 1;
        issues.push({
          rule: rule.name,
          points: rule.points,
          line: lineNum,
          match: match,
        });
      }
    }
  }

  return issues;
}

function main() {
  console.log('\n📝 Copy Quality Linter\n');
  console.log('─'.repeat(50));

  let totalPenalty = 0;
  const allIssues = [];

  for (const scanDir of SCAN_DIRS) {
    const files = findFiles(scanDir);
    for (const file of files) {
      const issues = lintFile(file);
      if (issues.length > 0) {
        allIssues.push({ file, issues });
        for (const issue of issues) {
          totalPenalty += issue.points;
        }
      }
    }
  }

  // Report issues
  if (allIssues.length > 0) {
    console.log('\n⚠️  Issues found:\n');
    for (const { file, issues } of allIssues) {
      console.log(`  ${file}:`);
      for (const issue of issues) {
        console.log(`    L${issue.line}: ${issue.rule} (-${issue.points})`);
      }
    }
  } else {
    console.log('\n✨ No issues found!');
  }

  // Calculate score
  const score = Math.max(0, MAX_SCORE - totalPenalty);
  const passed = score >= MIN_PASSING;

  console.log('\n' + '─'.repeat(50));
  console.log(`\n  Score: ${score}/${MAX_SCORE}`);
  console.log(`  Status: ${passed ? '✅ PASS' : '❌ FAIL'}\n`);

  if (!passed) {
    console.log(`  Build failed: score ${score} is below minimum ${MIN_PASSING}\n`);
    process.exit(1);
  }

  process.exit(0);
}

main();
