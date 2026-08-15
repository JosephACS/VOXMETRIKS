import { test, expect, type APIRequestContext, type Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import zlib from 'node:zlib';

/**
 * Spec 051 — fail-closed Playwright suite on an isolated DuckDB + API.
 * NEVER points DB_PATH at data/warehouse/voxmetrik.duckdb.
 */

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8010/api/v1';
const API_ORIGIN = API.replace(/\/api\/v1\/?$/, '');
const PERSONAS_PATH =
  process.env.E2E_051_PERSONAS ||
  path.join(process.env.TEMP || os.tmpdir(), 'voxmetrik-051-e2e', 'personas.json');

const VIEWPORTS = [
  { name: 'desktop', width: 1366, height: 768 },
  { name: 'mobile', width: 390, height: 844 },
] as const;

interface Persona {
  email: string;
  username: string;
  password: string;
  token: string;
  artistProfileId?: number;
  orgId?: number;
  artists?: { id: number }[];
}

interface PersonasFile {
  apiBase: string;
  password: string;
  platformAdmin: Persona;
  listener: Persona;
  owner: Persona;
  administrator: Persona;
  collaborator: Persona;
  reader: Persona;
  labelManager: Persona;
}

function loadPersonas(): PersonasFile {
  if (!fs.existsSync(PERSONAS_PATH)) {
    throw new Error(
      `FAIL-CLOSED: personas file missing at ${PERSONAS_PATH}. Run npm run e2e:051`,
    );
  }
  return JSON.parse(fs.readFileSync(PERSONAS_PATH, 'utf8')) as PersonasFile;
}

function assertNotCanonicalDb(): void {
  const dbPath = (process.env.DB_PATH || '').replace(/\//g, '\\').toLowerCase();
  if (!dbPath) {
    throw new Error('FAIL-CLOSED: DB_PATH is unset — isolated harness required');
  }
  if (
    dbPath.endsWith('data\\warehouse\\voxmetrik.duckdb') ||
    dbPath.includes('\\data\\warehouse\\voxmetrik.duckdb')
  ) {
    throw new Error(`FAIL-CLOSED: DB_PATH points at canonical warehouse: ${process.env.DB_PATH}`);
  }
  if (!dbPath.includes('voxmetrik-051-e2e')) {
    throw new Error(`FAIL-CLOSED: DB_PATH must be under voxmetrik-051-e2e: ${process.env.DB_PATH}`);
  }
}

function minimalWav(durationMs = 200, sampleRate = 8000): Buffer {
  const n = Math.max(1, Math.floor((sampleRate * durationMs) / 1000));
  const pcm = Buffer.alloc(n * 2);
  // Unique content each call — media store rejects duplicate audio hashes.
  for (let i = 0; i < pcm.length; i += 2) {
    pcm.writeInt16LE((Math.random() * 0xffff - 0x8000) | 0, i);
  }
  const dataSize = pcm.length;
  const hdr = Buffer.alloc(44);
  hdr.write('RIFF', 0);
  hdr.writeUInt32LE(36 + dataSize, 4);
  hdr.write('WAVE', 8);
  hdr.write('fmt ', 12);
  hdr.writeUInt32LE(16, 16);
  hdr.writeUInt16LE(1, 20);
  hdr.writeUInt16LE(1, 22);
  hdr.writeUInt32LE(sampleRate, 24);
  hdr.writeUInt32LE(sampleRate * 2, 28);
  hdr.writeUInt16LE(2, 32);
  hdr.writeUInt16LE(16, 34);
  hdr.write('data', 36);
  hdr.writeUInt32LE(dataSize, 40);
  return Buffer.concat([hdr, pcm]);
}

function minimalPng(width = 512, height = 512): Buffer {
  const crcTable: number[] = [];
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crcTable[n] = c >>> 0;
  }
  const crc32 = (buf: Buffer) => {
    let c = 0xffffffff;
    for (let i = 0; i < buf.length; i += 1) c = crcTable[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (tag: string, data: Buffer) => {
    const type = Buffer.from(tag);
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length, 0);
    const body = Buffer.concat([type, data]);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(body), 0);
    return Buffer.concat([len, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  // Mostly flat cover with a unique first-pixel stamp (hash must differ across uploads).
  const stamp = [
    (Math.random() * 256) | 0,
    (Math.random() * 256) | 0,
    (Math.random() * 256) | 0,
  ];
  const rows: Buffer[] = [];
  for (let y = 0; y < height; y += 1) {
    const row = Buffer.alloc(1 + width * 3, 0x40);
    if (y === 0) {
      row[1] = stamp[0];
      row[2] = stamp[1];
      row[3] = stamp[2];
    }
    rows.push(row);
  }
  const raw = Buffer.concat(rows);
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

async function rewriteApiToIsolated(page: Page): Promise<void> {
  await page.route(/\/api\/v1\//, async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const target = new URL(API_ORIGIN);
    url.protocol = target.protocol;
    url.host = target.host;
    await route.continue({ url: url.toString() });
  });
}

async function login(page: Page, user: Persona): Promise<void> {
  await rewriteApiToIsolated(page);
  await page.goto('/login');
  await page.evaluate(() => {
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch {
      /* ignore */
    }
  });
  await page.context().clearCookies();
  await page.goto('/login');
  await expect(page.locator('#loginId')).toBeVisible({ timeout: 45_000 });
  await page.locator('#loginId').fill(user.email === 'admin' ? 'admin' : user.email);
  await page.locator('#password').fill(user.password);
  await page.locator('button.submit-btn[type="submit"]').click();
  await page.waitForURL(
    /\/(discover|workpanel|welcome|spaces|artist-space|first-access|account|platform-ops|catalog|organizations)/,
    { timeout: 60_000 },
  );
}

async function pageAuthToken(page: Page): Promise<string> {
  const token = await page.evaluate(
    () => localStorage.getItem('voxmetrik_auth_token') ?? sessionStorage.getItem('voxmetrik_auth_token'),
  );
  expect(token, 'page must hold auth token after login').toBeTruthy();
  return token as string;
}

async function activateArtistSpace(page: Page, artistProfileId: number): Promise<void> {
  await rewriteApiToIsolated(page);
  const token = await pageAuthToken(page);
  const res = await page.request.post(`${API}/session/context`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    data: { space_key: `artist:${artistProfileId}` },
  });
  expect(res.ok(), `POST /session/context artist:${artistProfileId} → ${res.status()}`).toBeTruthy();
  await page.evaluate(
    ({ key, id }) => {
      localStorage.setItem(
        key,
        JSON.stringify({ id: `artist:${id}`, kind: 'artist', artistProfileId: id }),
      );
    },
    { key: 'voxmetriks_active_space_v1', id: artistProfileId },
  );
  await page.goto('/artist-space');
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
  await expect(page).not.toHaveURL(/\/artist-space\/claim/);
}

async function activateOrgSpace(page: Page, orgId: number): Promise<void> {
  await rewriteApiToIsolated(page);
  const token = await pageAuthToken(page);
  const res = await page.request.post(`${API}/session/context`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    data: { space_key: `organization:${orgId}` },
  });
  expect(res.ok(), `POST /session/context organization:${orgId} → ${res.status()}`).toBeTruthy();
  await page.evaluate(
    ({ key, id }) => {
      localStorage.setItem(
        key,
        JSON.stringify({ id: `org:${id}`, kind: 'organization', organizationId: id }),
      );
    },
    { key: 'voxmetriks_active_space_v1', id: orgId },
  );
  await page.goto('/catalog');
  await expect(page.getByTestId('app-shell')).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('heading', { name: /onboarding inicial/i })).toHaveCount(0);
}

async function prepareDraftOnReview(page: Page, title: string): Promise<void> {
  await expect(page.getByTestId('release-title')).toBeVisible({ timeout: 20_000 });
  await page.getByTestId('release-title').fill(title);
  const steps = page.locator('nav.stepper button.step');
  await steps.nth(1).click();
  const trackTitle = page
    .locator('.wizard-form [formarrayname="tracks"] input[formcontrolname="title"]')
    .first();
  await expect(trackTitle).toBeVisible({ timeout: 10_000 });
  await trackTitle.fill(`${title} · Track 1`);
  await steps.nth(5).click();
  await expect(page.getByTestId('wizard-save')).toBeVisible({ timeout: 15_000 });
}

function publishingBase(artistProfileId: number): string {
  return `${API}/artist-space/${artistProfileId}/publishing`;
}

/** Persist draft via UI; wait for create response + full save (not draft-id alone — that appears mid-save). */
async function saveDraftFromReview(
  page: Page,
): Promise<{ id: number; status: string; title: string }> {
  const createPromise = page.waitForResponse((r) => {
    try {
      const u = new URL(r.url());
      return (
        /\/api\/v1\/artist-space\/\d+\/publishing\/releases$/.test(u.pathname) &&
        r.request().method() === 'POST'
      );
    } catch {
      return false;
    }
  }, { timeout: 60_000 });

  await expect(page.getByTestId('wizard-save')).toBeEnabled({ timeout: 10_000 });
  await page.getByTestId('wizard-save').click();

  const createRes = await createPromise;
  const createBodyText = await createRes.text();
  expect(createRes.ok(), `create draft → ${createRes.status()} ${createBodyText}`).toBeTruthy();
  const created = JSON.parse(createBodyText) as { id: number; status: string; title: string };
  expect(created.id).toBeTruthy();
  expect(created.status).toBe('draft');

  // Full save finishes with success banner and/or navigation to music (after tracks persist).
  await expect
    .poll(
      async () => {
        const err = page.locator('app-enterprise-error-state');
        if (await err.isVisible().catch(() => false)) {
          throw new Error(`wizard save failed: ${(await err.innerText()).slice(0, 400)}`);
        }
        if (await page.getByTestId('wizard-info').isVisible().catch(() => false)) return 'info';
        if (/\/artist-space\/music/.test(page.url())) return 'music';
        return null;
      },
      { timeout: 60_000 },
    )
    .toBeTruthy();

  return created;
}

async function apiGetRelease(
  request: APIRequestContext,
  token: string,
  artistProfileId: number,
  submissionId: number,
): Promise<{ id: number; title: string; status: string }> {
  const res = await request.get(
    `${publishingBase(artistProfileId)}/releases/${submissionId}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  expect(res.ok(), `get release ${submissionId} → ${res.status()}`).toBeTruthy();
  const body = (await res.json()) as {
    submission?: { id: number; title: string; status: string };
    id?: number;
    title?: string;
    status?: string;
  };
  const sub = body.submission ?? body;
  expect(sub.id).toBe(submissionId);
  return sub as { id: number; title: string; status: string };
}

async function apiListReleases(
  request: APIRequestContext,
  token: string,
  artistProfileId: number,
): Promise<Array<{ id: number; title: string; status: string }>> {
  const res = await request.get(`${publishingBase(artistProfileId)}/releases`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(res.ok(), `list releases → ${res.status()}`).toBeTruthy();
  return (await res.json()) as Array<{ id: number; title: string; status: string }>;
}

async function apiMakeSubmissionReady(
  request: APIRequestContext,
  token: string,
  artistProfileId: number,
  submissionId: number,
): Promise<void> {
  const auth = { Authorization: `Bearer ${token}` };
  const loadDetail = async () => {
    const detail = await request.get(
      `${publishingBase(artistProfileId)}/releases/${submissionId}`,
      { headers: auth },
    );
    expect(detail.ok(), `detail ${submissionId} → ${detail.status()}`).toBeTruthy();
    return (await detail.json()) as {
      tracks?: Array<{ id: number; audio_media_id?: number | null }>;
      submission?: { id: number; cover_media_id?: number | null };
    };
  };

  // Wizard may still be finishing persistTracks; wait until at least one track exists.
  let body = await loadDetail();
  await expect
    .poll(
      async () => {
        body = await loadDetail();
        return body.tracks?.length ?? 0;
      },
      { timeout: 30_000 },
    )
    .toBeGreaterThan(0);

  const tracks = body.tracks ?? [];
  for (const tr of tracks) {
    if (tr.audio_media_id) continue;
    const audio = await request.post(
      `${publishingBase(artistProfileId)}/releases/${submissionId}/tracks/${tr.id}/audio`,
      {
        headers: auth,
        multipart: {
          file: {
            name: 't.wav',
            mimeType: 'audio/wav',
            buffer: minimalWav(),
          },
        },
      },
    );
    expect(audio.ok(), `upload audio track ${tr.id} → ${audio.status()} ${await audio.text()}`).toBeTruthy();
  }

  body = await loadDetail();
  if (!body.submission?.cover_media_id) {
    const cover = await request.post(
      `${publishingBase(artistProfileId)}/releases/${submissionId}/cover`,
      {
        headers: auth,
        multipart: {
          file: {
            name: 'c.png',
            mimeType: 'image/png',
            buffer: minimalPng(512, 512),
          },
        },
      },
    );
    expect(cover.ok(), `upload cover → ${cover.status()} ${await cover.text()}`).toBeTruthy();
  }

  // Gate: every track must have audio before submit.
  body = await loadDetail();
  for (const tr of body.tracks ?? []) {
    expect(tr.audio_media_id, `track ${tr.id} must have audio_media_id`).toBeTruthy();
  }
  expect(body.submission?.cover_media_id, 'cover_media_id required').toBeTruthy();
}

async function apiSubmit(
  request: APIRequestContext,
  token: string,
  artistProfileId: number,
  submissionId: number,
): Promise<{ id: number; status: string }> {
  const res = await request.post(
    `${publishingBase(artistProfileId)}/releases/${submissionId}/submit`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  expect(res.ok(), `submit → ${res.status()} ${await res.text()}`).toBeTruthy();
  return (await res.json()) as { id: number; status: string };
}

async function apiHistory(
  request: APIRequestContext,
  token: string,
  artistProfileId: number,
  submissionId: number,
): Promise<unknown[]> {
  const res = await request.get(
    `${publishingBase(artistProfileId)}/releases/${submissionId}/history`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  expect(res.ok(), `history → ${res.status()}`).toBeTruthy();
  const body = await res.json();
  return Array.isArray(body) ? body : body?.items || [];
}

test.beforeAll(async ({ request }) => {
  assertNotCanonicalDb();
  const health = await request.get(`${API_ORIGIN}/api/v1/health`);
  expect(health.ok(), 'isolated API health must succeed').toBeTruthy();
  const openapi = await request.get(`${API_ORIGIN}/openapi.json`);
  expect(openapi.ok()).toBeTruthy();
  const body = (await openapi.json()) as { paths: Record<string, unknown> };
  expect(body.paths['/api/v1/artist-access/discover']).toBeTruthy();
  expect(body.paths['/api/v1/platform/catalog-reviews']).toBeTruthy();
  const personas = loadPersonas();
  expect(personas.owner.artistProfileId).toBeTruthy();
  expect(personas.labelManager.orgId).toBeTruthy();
  expect(personas.administrator.artistProfileId).toBeTruthy();
  expect(personas.collaborator.artistProfileId).toBeTruthy();
  expect(personas.reader.artistProfileId).toBeTruthy();
});

for (const vp of VIEWPORTS) {
  test.describe(`Artist professional journey ${vp.name}`, () => {
    test.use({ viewport: { width: vp.width, height: vp.height } });

    test('listener reaches claim wizard choice modes (create/access entry)', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.listener);
      await page.goto('/artist-space/claim');
      await expect(page.getByTestId('choice-discover')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId('choice-create')).toBeVisible();
    });

    test('discovery empty path does not invent matches', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.listener);
      await page.goto('/artist-space/claim');
      await page.getByTestId('choice-discover').click();
      await page.getByTestId('discover-query').fill('Artista Inexistente XYZ 051');
      await page.getByRole('button', { name: /buscar|search/i }).click();
      await expect(page.getByTestId('discover-empty')).toBeVisible({ timeout: 25_000 });
    });

    test('approved owner opens Artist Space music and profile', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.owner);
      await activateArtistSpace(page, p.owner.artistProfileId!);
      await page.goto('/artist-space/music');
      await expect(page.getByTestId('tab-releases')).toBeVisible({ timeout: 20_000 });
      await page.goto('/artist-space/profile');
      await expect(page.getByRole('heading', { level: 1, name: /perfil|profile/i })).toBeVisible({
        timeout: 20_000,
      });
    });

    test('administrator can open release wizard', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.administrator);
      await activateArtistSpace(page, p.administrator.artistProfileId!);
      await page.goto('/artist-space/releases/new');
      await expect(page.getByTestId('release-title')).toBeVisible({ timeout: 20_000 });
    });

    test('reader cannot open new release wizard', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.reader);
      await activateArtistSpace(page, p.reader.artistProfileId!);
      await page.goto('/artist-space/releases/new');
      await expect(page.getByTestId('wizard-save')).toHaveCount(0, { timeout: 15_000 });
      await expect(page.getByTestId('release-title')).toHaveCount(0);
    });

    test('collaborator saves a real draft; submit stays forbidden', async ({ page, request }) => {
      const p = loadPersonas();
      const artistId = p.collaborator.artistProfileId!;
      await login(page, p.collaborator);
      await activateArtistSpace(page, artistId);
      await page.goto('/artist-space/releases/new');
      const title = `Collab Draft ${vp.name} ${Date.now()}`;
      await prepareDraftOnReview(page, title);
      await expect(page.getByTestId('submit-forbidden')).toBeVisible({ timeout: 10_000 });
      await expect(page.getByTestId('submit-now')).toHaveCount(0);
      const created = await saveDraftFromReview(page);
      expect(created.title).toBe(title);

      const token = await pageAuthToken(page);
      const draft = await apiGetRelease(request, token, artistId, created.id);
      expect(draft.status).toBe('draft');
      expect(draft.title).toBe(title);
      const listed = await apiListReleases(request, token, artistId);
      expect(listed.some((r) => r.id === created.id && r.status === 'draft')).toBeTruthy();
    });

    test('owner submits independent release; platform review cycle publishes', async ({
      page,
      request,
    }) => {
      const p = loadPersonas();
      const artistId = p.owner.artistProfileId!;
      const title = `Owner Publish ${vp.name} ${Date.now()}`;

      await login(page, p.owner);
      await activateArtistSpace(page, artistId);
      await page.goto('/artist-space/releases/new');
      await prepareDraftOnReview(page, title);
      await expect(page.getByTestId('submit-now')).toBeVisible({ timeout: 10_000 });
      const created = await saveDraftFromReview(page);
      expect(created.title).toBe(title);
      expect(created.status).toBe('draft');
      const submissionId = created.id;

      const ownerToken = await pageAuthToken(page);
      const draft = await apiGetRelease(request, ownerToken, artistId, submissionId);
      expect(draft.status).toBe('draft');

      await apiMakeSubmissionReady(request, ownerToken, artistId, submissionId);
      const submitted = await apiSubmit(request, ownerToken, artistId, submissionId);
      expect(['submitted', 'under_review']).toContain(submitted.status);
      const historyAfterSubmit = await apiHistory(request, ownerToken, artistId, submissionId);
      const historyLenAfterSubmit = historyAfterSubmit.length;
      expect(historyLenAfterSubmit).toBeGreaterThan(0);

      // Empty notes on an existing submission must be validation — never 404.
      const emptyNotes = await request.post(
        `${API}/platform/catalog-reviews/${submissionId}/request-changes`,
        {
          headers: {
            Authorization: `Bearer ${p.platformAdmin.token}`,
            'Content-Type': 'application/json',
          },
          data: { notes: '   ' },
        },
      );
      expect([400, 422]).toContain(emptyNotes.status());
      expect(emptyNotes.status()).not.toBe(404);

      await login(page, p.platformAdmin);
      await page.goto('/platform-ops/catalog-reviews');
      await expect(
        page.getByRole('heading', { name: /revisiones independientes|independent reviews/i }),
      ).toBeVisible({ timeout: 20_000 });
      const chip = page.getByRole('button', { name: /en revisión|in review/i });
      await expect(chip).toBeVisible();
      const filterReq = page.waitForRequest(
        (r) =>
          r.url().includes('/platform/catalog-reviews') &&
          r.url().includes('status=under_review'),
      );
      await chip.click();
      await filterReq;
      await expect(page.getByText(title)).toBeVisible({ timeout: 25_000 });

      const changes = await request.post(
        `${API}/platform/catalog-reviews/${submissionId}/request-changes`,
        {
          headers: {
            Authorization: `Bearer ${p.platformAdmin.token}`,
            'Content-Type': 'application/json',
          },
          data: { notes: `Please fix metadata ${vp.name}` },
        },
      );
      expect(changes.ok(), `request-changes → ${changes.status()}`).toBeTruthy();
      const afterChanges = (await changes.json()) as { status: string };
      expect(afterChanges.status).toBe('changes_requested');

      const patch = await request.patch(
        `${publishingBase(artistId)}/releases/${submissionId}`,
        {
          headers: {
            Authorization: `Bearer ${ownerToken}`,
            'Content-Type': 'application/json',
          },
          data: { title: `${title} · revised` },
        },
      );
      expect(patch.ok(), `owner edit → ${patch.status()}`).toBeTruthy();
      const resubmitted = await apiSubmit(request, ownerToken, artistId, submissionId);
      expect(['submitted', 'under_review']).toContain(resubmitted.status);

      const approved = await request.post(
        `${API}/platform/catalog-reviews/${submissionId}/approve`,
        {
          headers: {
            Authorization: `Bearer ${p.platformAdmin.token}`,
            'Content-Type': 'application/json',
          },
          data: { notes: 'Looks good' },
        },
      );
      expect(approved.ok(), `approve → ${approved.status()} ${await approved.text()}`).toBeTruthy();

      const published = await request.post(
        `${API}/platform/catalog-reviews/${submissionId}/publish`,
        {
          headers: {
            Authorization: `Bearer ${p.platformAdmin.token}`,
            'Content-Type': 'application/json',
          },
          data: { idempotency_key: `e2e-051-${submissionId}-${vp.name}` },
        },
      );
      expect(published.ok(), `publish → ${published.status()} ${await published.text()}`).toBeTruthy();

      const finalList = await apiListReleases(request, ownerToken, artistId);
      const final = finalList.find((r) => r.id === submissionId);
      expect(final?.status).toBe('published');

      const historyFinal = await apiHistory(request, ownerToken, artistId, submissionId);
      expect(historyFinal.length).toBeGreaterThanOrEqual(historyLenAfterSubmit);
      // Append-only: prior length never shrinks after later decisions.
      expect(historyFinal.length).toBeGreaterThan(historyLenAfterSubmit);
    });

    test('organization catalog requires explicit artist selection', async ({ page }) => {
      const p = loadPersonas();
      expect(p.labelManager.orgId).toBeTruthy();
      await login(page, p.labelManager);
      await activateOrgSpace(page, p.labelManager.orgId!);
      await page.goto('/artist/releases/new');
      const artistSelect = page.getByTestId('artist-select');
      await expect(artistSelect).toBeVisible({ timeout: 25_000 });
      await expect(artistSelect.locator('option')).toHaveCount(3, { timeout: 15_000 });
      await expect
        .poll(async () => artistSelect.evaluate((el) => (el as HTMLSelectElement).selectedIndex))
        .toBe(0);
      await page.getByTestId('release-title').fill(`E2E Explicit Artist 051 ${vp.name}`);
      await expect(
        page.getByText(/elige uno explícitamente|choose one explicitly/i),
      ).toBeVisible();
      await artistSelect.selectOption({ index: 1 });
      await expect
        .poll(async () => artistSelect.evaluate((el) => (el as HTMLSelectElement).selectedIndex))
        .toBe(1);
      const selectedLabel = await artistSelect.evaluate(
        (el) => (el as HTMLSelectElement).selectedOptions[0]?.textContent?.trim() || '',
      );
      expect(selectedLabel.length).toBeGreaterThan(0);
      expect(selectedLabel).not.toMatch(/selecciona|select an artist/i);
    });

    test('legacy artist-space tracks/releases redirect away from split URLs', async ({ page }) => {
      const p = loadPersonas();
      await login(page, p.listener);
      await page.goto('/artist-space/tracks');
      await expect(page).not.toHaveURL(/\/artist-space\/tracks$/);
      await page.goto('/artist-space/releases');
      await expect(page).not.toHaveURL(/\/artist-space\/releases$/);
    });
  });
}
