
new MutationObserver(muts => {
  for (const m of muts) for (const n of m.addedNodes) {
    if (n.id === TID || (n.querySelector && n.querySelector('#' + TID))) {
      const el = n.id === TID ? n : n.querySelector('#' + TID);
      handle(el);
    }
  }
}).observe(document.documentElement, { childList: true, subtree: true });

async function handle(el) {
  try {
    const req = el.textContent.trim() ? JSON.parse(el.textContent) : { cmd: 'cookies' };
    const cmd = req.cmd || 'cookies';
    let resp;
    if (cmd === 'cookies') {
      resp = await chrome.runtime.sendMessage({ action: 'cookies', url: req.url || location.href });
    } else if (cmd === 'cdp') {
      resp = await chrome.runtime.sendMessage({ action: 'cdp', method: req.method, params: req.params || {}, tabId: req.tabId });
    } else if (cmd === 'batch') {
      resp = await chrome.runtime.sendMessage({ action: 'batch', commands: req.commands, tabId: req.tabId });
    } else if (cmd === 'tabs') {
      resp = await chrome.runtime.sendMessage({ action: 'tabs', method: req.method, tabId: req.tabId });
    } else {
      resp = { ok: false, error: 'unknown cmd: ' + cmd };
    }
    el.textContent = JSON.stringify(resp);
  } catch (e) {
    el.textContent = JSON.stringify({ ok: false, error: e.message });
  }
}