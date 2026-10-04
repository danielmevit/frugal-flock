// Frugal Flock — Copyright (C) 2026 Daniel Mitev
// Public attribution: Daniel Mevit (@danielmevit)
// Original project: https://github.com/danielmevit/frugal-flock
// SPDX-License-Identifier: AGPL-3.0-only
// Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
// See LICENSE and NOTICE; distributed without warranty.
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const fs = require("node:fs");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");
(async () => {
  const browser = await chromium.launch({
    ...(process.env.M2_CHROMIUM_PATH
      ? { executablePath: process.env.M2_CHROMIUM_PATH }
      : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const failures = [],
    external = [];
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("request", (request) => {
    if (/^https?:/.test(request.url())) external.push(request.url());
  });
  const output = process.env.M2_SCREENSHOTS;
  const shot = async (name) => {
    if (output) {
      fs.mkdirSync(output, { recursive: true });
      await page.screenshot({
        path: path.join(output, name + ".png"),
        fullPage: true,
      });
    }
  };
  const click = (label) =>
    page.getByRole("button", { name: label, exact: true }).click();
  const heading = async (label) =>
    assert.equal(await page.locator("h1").textContent(), label);
  try {
    await page.goto(
      pathToFileURL(path.resolve(__dirname, "../index.html")).href,
    );
    await heading("One conversation. A small next step.");
    await shot("welcome");
    await click("Open sample project");
    await click("Connect sample tool");
    assert.equal(
      await page
        .locator("#conversation-title")
        .evaluate((e) => e === document.activeElement),
      true,
    );
    const request = page.getByLabel("Describe a change");
    assert.ok(
      (await page.locator(".field-hint").textContent()).includes(
        "Ctrl/Command+Enter",
      ),
    );
    await page.evaluate(() => {
      window.shortcutSubmits = 0;
      document.addEventListener("submit", () => window.shortcutSubmits++);
    });
    // Browser required validation must reject empty text without a submit event.
    await request.fill("");
    await request.press("Control+Enter");
    await heading("What would you like to build?");
    assert.equal(await page.evaluate(() => window.shortcutSubmits), 0);
    // Trimmed validation uses the same submit path as the visible button.
    await request.fill("   ");
    await request.press("Meta+Enter");
    await heading("What would you like to build?");
    assert.equal(await page.locator("#error").isVisible(), true);
    assert.equal(await page.evaluate(() => window.shortcutSubmits), 1);
    await request.fill("Search");
    await request.press("End");
    await request.press("Enter");
    assert.equal(await request.inputValue(), "Search\n");
    await heading("What would you like to build?");
    await request.evaluate((textarea) => {
      for (const extra of [
        { repeat: true },
        { isComposing: true },
        { altKey: true },
        { shiftKey: true },
      ]) {
        const event = new KeyboardEvent("keydown", {
          bubbles: true,
          cancelable: true,
          key: "Enter",
          ctrlKey: true,
          ...extra,
        });
        textarea.dispatchEvent(event);
        if (event.defaultPrevented)
          throw new Error("unrelated/repeated shortcut prevented");
      }
    });
    await page.locator("#conversation-title").focus();
    await page.keyboard.press("Control+Enter");
    await page.evaluate(() => {
      const textarea = document.createElement("textarea");
      document.body.append(textarea);
      const event = new KeyboardEvent("keydown", {
        bubbles: true,
        cancelable: true,
        key: "Enter",
        metaKey: true,
      });
      textarea.dispatchEvent(event);
      textarea.remove();
      if (event.defaultPrevented)
        throw new Error("shortcut outside form prevented");
    });
    await heading("What would you like to build?");
    assert.equal(await page.evaluate(() => window.shortcutSubmits), 1);
    await request.fill('<img src=x onerror="alert(1)"> Search by title');
    await request.press("Control+Enter");
    assert.equal(await page.evaluate(() => window.shortcutSubmits), 2);
    await heading("A plan you can review.");
    assert.equal(await page.locator("#conversation-body img").count(), 0);
    assert.ok(
      (await page.locator("#conversation-body").textContent()).includes(
        "<img src=x",
      ),
    );
    await click("Restart demo");
    await click("Open sample project");
    await click("Connect sample tool");
    await click("Create plan");
    await shot("plan");
    await click("Approve and start");
    await click("Show next sample event");
    await page.getByLabel("Your answer").fill("Titles and text.");
    await page.getByLabel("Your answer").press("Meta+Enter");
    await click("Show next sample event");
    await heading("Keep the work. Choose what follows.");
    await shot("limit");
    assert.equal(
      await page
        .getByRole("button", { name: "Apply changes", exact: true })
        .count(),
      0,
    );
    await click("Continue with Grok");
    await click("Show next sample event");
    await heading("The work finished. Checks come next.");
    await click("Show check results");
    await heading("A second look at the result.");
    await click("Show reviewer decision");
    await heading("Ready for your review.");
    await shot("review");
    await page
      .getByLabel("What should change?")
      .fill("Use a clearer empty-state message.");
    await page.getByLabel("What should change?").press("Control+Enter");
    await heading("A plan you can review.");
    assert.equal(
      await page
        .getByRole("button", { name: "Apply changes", exact: true })
        .count(),
      0,
    );
    await click("Approve and start");
    await click("Stop");
    await heading("Work stopped. Context stays here.");
    await click("Restart demo");
    await click("Open sample project");
    await click("Connect sample tool");
    await click("Create plan");
    await click("Approve and start");
    await click("Show next sample event");
    await click("Send answer");
    await click("Show next sample event");
    await click("Continue with Grok");
    await click("Show next sample event");
    await click("Show check results");
    await click("Show reviewer decision");
    await click("Apply changes");
    await heading("A small change, reviewed and applied.");
    assert.ok(
      (await page.locator("#conversation-body").textContent()).includes(
        "Your real project has not changed.",
      ),
    );
    await shot("applied");
    await page.setViewportSize({ width: 390, height: 844 });
    await click("Restart demo");
    await shot("mobile");
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    );
    assert.equal(
      await page.locator(".inspector-disclosure").getAttribute("open"),
      null,
    );
    await page.keyboard.press("Tab");
    assert.ok(
      await page.evaluate(() => document.activeElement.tagName === "BUTTON"),
    );
    assert.deepEqual(failures, []);
    assert.deepEqual(external, []);
    console.log(
      "browser: full journey, Ctrl/Command+Enter once, plain Enter, required/trimmed validation, ignored repeated/composing/unrelated/outside-form keys, replacement/acceptance, revisions, Stop, focus, escaped text, narrow layout, no external requests or page errors passed",
    );
  } finally {
    await context.close();
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
