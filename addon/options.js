document.getElementById('save').addEventListener('click', async () => {
  const token = document.getElementById('token').value.trim();
  if (!/^[A-Za-z0-9_-]{43}$/.test(token)) { document.getElementById('status').textContent = 'Bitte den vollständigen Code aus der IC35-App einfügen.'; return; }
  await browser.storage.local.set({token});
  document.getElementById('token').value = '';
  document.getElementById('status').textContent = 'Code gespeichert. Verbindung wird hergestellt …';
});
document.getElementById('forget').addEventListener('click', async () => {
  await browser.storage.local.remove('token');
  document.getElementById('token').value = '';
});
setInterval(async () => {
  const result = await browser.runtime.sendMessage({type: 'status'});
  document.getElementById('status').textContent = result.status;
}, 2000);
