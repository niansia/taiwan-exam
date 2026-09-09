#!/usr/bin/env node
/* Measure fixed-page overflow in generated GSAT review HTML. */

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const [directory, executable] = process.argv.slice(2);
  if (!directory || !executable) {
    throw new Error("usage: qa_gsat_internal_layout.js HTML_DIRECTORY BROWSER_EXECUTABLE");
  }
  const browser = await chromium.launch({ headless: true, executablePath: executable });
  const report = [];
  try {
    for (const name of fs.readdirSync(directory).filter((x) => x.endsWith("_學生卷.html")).sort()) {
      const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
      await page.goto("file:///" + path.resolve(directory, name).replace(/\\/g, "/"), { waitUntil: "load" });
      await page.emulateMedia({ media: "print" });
      const measurements = await page.locator(".content").evaluateAll((nodes) => nodes.map((node, index) => ({
        page: index + 2,
        clientHeight: node.clientHeight,
        scrollHeight: node.scrollHeight,
        overflowPx: Math.max(0, node.scrollHeight - node.clientHeight),
        textChars: (node.innerText || "").replace(/\s+/g, "").length,
      })));
      report.push({
        file: name,
        status: measurements.every((x) => x.overflowPx === 0) ? "pass" : "fail",
        measurements,
      });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  const payload = { status: report.every((x) => x.status === "pass") ? "pass" : "fail", papers: report };
  fs.writeFileSync(path.join(directory, "HTML頁框溢位檢核.json"), JSON.stringify(payload, null, 2));
  process.stdout.write(JSON.stringify(payload, null, 2));
  process.exitCode = payload.status === "pass" ? 0 : 2;
}

main().catch((error) => {
  process.stderr.write(String(error.stack || error));
  process.exitCode = 2;
});
