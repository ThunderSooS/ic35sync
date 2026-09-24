const endpoint = 'http://127.0.0.1:5234';
const session = crypto.randomUUID();
let status = 'Noch nicht gekoppelt';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
browser.browserAction.onClicked.addListener(() => browser.runtime.openOptionsPage());
browser.runtime.onInstalled.addListener(() => browser.runtime.openOptionsPage());
browser.runtime.onMessage.addListener(message => message?.type === 'status' ? Promise.resolve({status}) : undefined);

async function post(path, config, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(endpoint + path, {
      method: 'POST', cache: 'no-store', credentials: 'omit', signal: controller.signal,
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config.token},
      body: JSON.stringify({protocol: 1, profile: config.profile, session, version: browser.runtime.getManifest().version, ...data}),
    });
    if (!response.ok) throw new Error(response.status === 403 ? 'Kopplungscode oder Thunderbird-Profil passt nicht.' : 'Verbindung abgelehnt (' + response.status + ')');
    return response.json();
  } finally { clearTimeout(timer); }
}

(async function loop() {
  let config = await browser.storage.local.get(['token', 'profile']);
  if (!config.profile) await browser.storage.local.set({profile: crypto.randomUUID()});
  while (true) {
    config = await browser.storage.local.get(['token', 'profile']);
    if (!config.token) { status = 'Kopplungscode aus der IC35-App eingeben.'; await pause(1500); continue; }
    try {
      const job = await post('/poll', config, {});
      status = 'Mit der IC35-App verbunden. Kalender dort auswählen.';
      if (job.id) {
        let reply;
        try {
          const result = JSON.parse(await browser.ic35Calendar.execute(JSON.stringify(job)));
          if (!result.ok) throw new Error(result.error);
          reply = {id: job.id, ok: true, data: result.data};
        } catch (e) {
          reply = {id: job.id, ok: false, error: String(e.message || e).slice(0, 1000)};
        }
        // Retry only the reply, NEVER a calendar write after an uncertain result.
        for (let attempt = 0; attempt < 3; attempt++) {
          try { await post('/result', config, reply); break; }
          catch (e) { if (attempt === 2) throw e; await pause(1000); }
        }
      }
    } catch (e) {
      status = 'Nicht verbunden: ' + String(e.message || e);
      await pause(2000);
    }
  }
})();
