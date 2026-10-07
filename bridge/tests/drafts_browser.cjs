// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");
(async () => {
  assert.ok(process.env.TMPDIR, "Set workspace-local TMPDIR");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "draft-ui-"));
  for (const name of ["repo", "coord", "wt"])
    fs.mkdirSync(path.join(fixture, name));
  const engine = path.join(fixture, "watch-fixture");
  fs.writeFileSync(
    engine,
    `#!/usr/bin/env python3\nimport json,sys\nassert sys.argv[1:] == ['watch','--once','--json']\nprint(json.dumps(dict(schema_version=1,observed_at='2026-10-05T00:00:00Z',stopped=False,agents=[],results=[],retries=[],recent_events=[],warnings=[],evidence='recorded only')))\n`,
    { mode: 0o755 },
  );
  const child = spawn(
    "python3",
    [
      "-B",
      path.resolve(__dirname, "../server.py"),
      "--project",
      fixture,
      "--engine",
      engine,
      "--enable-plan-drafts",
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  let stderr = "",
    browser,
    context;
  child.stderr.on("data", (data) => {
    stderr = (stderr + data).slice(-2000);
  });
  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error("startup timeout " + stderr)),
        10000,
      );
      child.once("error", (error) => {
        clearTimeout(timer);
        reject(error);
      });
      child.once("exit", (code) => {
        clearTimeout(timer);
        reject(new Error("startup exit " + code + " " + stderr));
      });
      child.stdout.on("data", (data) => {
        const url = data.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (url) {
          clearTimeout(timer);
          resolve(url[0]);
        }
      });
    });
    browser = await chromium.launch(
      process.env.M2_CHROMIUM_PATH
        ? { executablePath: process.env.M2_CHROMIUM_PATH }
        : {},
    );
    context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const failures = [],
      requests = [];
    let posts = 0;
    page.on("pageerror", (error) => failures.push(error.message));
    page.on("request", (request) => {
      requests.push({ url: request.url(), method: request.method() });
      if (request.method() === "POST") posts++;
    });
    await page.goto(origin);
    await page.waitForFunction(
      () =>
        !document.getElementById("manual-drafts").hidden &&
        !document.getElementById("save-draft").disabled,
    );
    const input = page.getByLabel("Describe the work to save");
    const save = page.getByRole("button", { name: "Save draft", exact: true });
    assert.equal(await page.locator("#mode-label").textContent(), "Manual drafts");
    assert.ok((await page.locator(".notice").textContent()).includes("no AI or worker starts"));
    assert.equal(await page.locator("#execution-panel").isVisible(), false);
    assert.equal(await page.locator("#reopen-job-form").isVisible(), false);
    assert.equal(await page.locator("#workspace-empty").isVisible(), true);
    await save.click();
    assert.equal(posts, 0);
    await input.fill("   ");
    await save.click();
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("Enter a request"),
    );
    assert.equal(posts, 0);
    const literal = "<img src=x onerror=alert(1)> Café\n$ text only\n" + "long_literal_request_".repeat(100);
    await input.fill(literal);
    await page.evaluate(() => {
      document
        .getElementById("draft-form")
        .dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
      document
        .getElementById("draft-form")
        .dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
    });
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("draft saved."),
    );
    assert.equal(posts, 1);
    assert.equal(await page.locator("#draft-text").textContent(), literal);
    assert.equal(await page.locator("#draft-result img").count(), 0);
    const identity = await page.getByLabel("Reopen a draft by ID").inputValue();
    assert.match(identity, /^[0-9a-f]{32}$/);
    const records = () =>
      fs
        .readdirSync(path.join(fixture, "coord/ui-plans"))
        .filter((name) => name.endsWith(".json"));
    assert.equal(records().length, 1);
    await page.reload();
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("draft reopened."),
    );
    assert.equal(posts, 1);
    assert.equal(await page.locator("#draft-text").textContent(), literal);
    await page.locator("#reopen-details > summary").click();
    await page.getByLabel("Reopen a draft by ID").fill("a".repeat(32));
    await page
      .getByRole("button", { name: "Reopen draft", exact: true })
      .click();
    await page.waitForFunction(() =>
      document.getElementById("draft-status").textContent.includes("not found"),
    );
    assert.equal(await page.locator("#draft-result").isVisible(), false);
    await input.fill("Preserve this new request");
    await page.route(
      origin + "/api/plans",
      (route) =>
        route.fulfill({
          status: 403,
          contentType: "application/json",
          body: '{"schema_version":1,"error":"session_refused"}',
        }),
      { times: 1 },
    );
    await save.click();
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("Session refreshed"),
    );
    assert.equal(posts, 2);
    assert.equal(records().length, 1);
    assert.equal(await input.inputValue(), "Preserve this new request");
    assert.equal(await page.locator("#draft-status").getAttribute("role"), "status");
    assert.equal(await page.locator("#draft-form").getAttribute("aria-busy"), "false");
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.setViewportSize({width:1440,height:900});
    assert.equal(await save.isEnabled(), true);
    await page.route(
      origin + "/api/plans",
      (route) =>
        route.fulfill({
          status: 503,
          contentType: "application/json",
          body: '{"schema_version":1,"error":"draft_unavailable"}',
        }),
      { times: 1 },
    );
    await save.click();
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("outcome not confirmed"),
    );
    assert.equal(posts, 3);
    assert.equal(records().length, 1);
    assert.equal(await input.inputValue(), "Preserve this new request");
    await save.click();
    await page.waitForFunction(() =>
      document
        .getElementById("draft-status")
        .textContent.includes("draft saved."),
    );
    assert.equal(posts, 4);
    assert.equal(records().length, 2);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    );
    await save.focus();
    await page.keyboard.press("Tab");
    await page.keyboard.press("Shift+Tab");
    assert.equal(await page.locator(":focus").getAttribute("id"), "save-draft");
    assert.ok(await save.evaluate((el) => getComputedStyle(el).outlineStyle !== "none"));
    assert.ok(await page.locator("#draft-text").evaluate((el) => el.scrollWidth <= el.clientWidth + 1));
    assert.deepEqual(failures, []);
    assert.ok(
      requests.every(
        (request) =>
          request.url.startsWith(origin + "/") &&
          ["GET", "POST"].includes(request.method),
      ),
    );
    assert.ok(
      requests
        .filter((request) => request.method === "POST")
        .every((request) => request.url === origin + "/api/plans"),
    );
    if (process.env.M2_SCREENSHOTS) {
      fs.mkdirSync(process.env.M2_SCREENSHOTS, { recursive: true });
      await page.screenshot({
        path: path.join(process.env.M2_SCREENSHOTS, "manual-draft-mobile.png"),
        fullPage: true,
      });
    }
    await page.route(
      origin + "/api/session",
      (route) =>
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: '{"schema_version":1,"manual_drafts":false,"token":null}',
        }),
      { times: 1 },
    );
    await page.route(
      origin + "/api/plans",
      (route) =>
        route.fulfill({
          status: 403,
          contentType: "application/json",
          body: '{"schema_version":1,"error":"session_refused"}',
        }),
      { times: 1 },
    );
    await save.click();
    await page.waitForFunction(
      () => document.getElementById("manual-drafts").hidden,
    );
    assert.ok(
      (await page.locator(".notice").textContent()).includes(
        "Read-only preview",
      ),
    );
    assert.equal(posts, 5);
    assert.equal(records().length, 2);
    assert.equal(await input.inputValue(), "Preserve this new request");
    console.log(
      "Draft UI: opt-in form, required/trimmed validation, one save on duplicate submit, escaped literal text, reload/reopen without POST, missing ID, stale-session and failed-save text preservation/no retry, explicit resave, mobile and no external requests/errors passed",
    );
    console.log("Fixture retained: " + fixture);
  } finally {
    if (context) await context.close();
    if (browser) await browser.close();
    if (child.exitCode === null) {
      child.kill("SIGINT");
      await Promise.race([
        once(child, "exit"),
        new Promise((resolve) => setTimeout(resolve, 2000)),
      ]);
      if (child.exitCode === null) child.kill("SIGKILL");
    }
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
