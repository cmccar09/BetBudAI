// @ts-check
const { defineConfig } = require('@playwright/test');

/**
 * Breakpoints match CLAUDE.md:
 *   mobile  < 640px  → 390px  (iPhone 14)
 *   tablet  640–1024 → 768px  (iPad portrait)
 *   desktop > 1024px → 1440px (standard laptop)
 *
 * isMobile in App.js fires at < 768px so both mobile + tablet
 * trigger the compact nav/layout.
 */
module.exports = defineConfig({
  testDir: './visual',
  timeout: 30_000,
  expect: {
    // Allow 2% pixel diff before failing a snapshot — handles
    // antialiasing and sub-pixel rendering differences between runs.
    toHaveScreenshot: { maxDiffPixelRatio: 0.02 },
  },
  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: 'http://localhost:3000',
    // Capture screenshot on every failure for CI/CD
    screenshot: 'only-on-failure',
    // Needed for fonts to load before screenshot
    actionTimeout: 10_000,
  },

  projects: [
    {
      name: 'mobile',
      use: {
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: 'tablet',
      use: {
        viewport: { width: 768, height: 1024 },
        deviceScaleFactor: 2,
      },
    },
    {
      name: 'desktop',
      use: {
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      },
    },
  ],

  webServer: {
    command: 'npm start --prefix ../frontend',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      // Silence the "open browser" CRA behaviour on Windows
      BROWSER: 'none',
    },
  },
});
