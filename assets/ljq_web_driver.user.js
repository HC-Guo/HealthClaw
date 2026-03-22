// ==UserScript==
// @name ljq_web_driver
// @namespace http://tampermonkey.net/
// @version 0.32
// @description Execute JS via ljq_web_driver
// @require https://code.jquery.com/jquery-3.6.0.min.js
// @author You
// @match *://*/*
// @grant GM_setValue
// @grant GM_getValue
// @grant GM_xmlhttpRequest
// @grant GM_openInTab
// @grant unsafeWindow
// @connect localhost
// @run-at document-start
// ==/UserScript==


(function() {
'use strict';
const log_prefix = "ljq_driver: ";

if (window.self !== window.top) {
window.addEventListener('message',e=>{if(e.data?.type==='ljq_exec'){try{let r=eval(e.data.code);parent.postMessage({type:'ljq_result',id:e.data.id,result:String(r)},'*')}catch(err){parent.postMessage({type:'ljq_result',id:e.data.id,error:err.message},'*')}}});
return;
}

const wsUrl = 'ws://localhost:18765';
const httpUrl = 'http://localhost:18766/';

function isWebSocketServerAlive(callback) {
GM_xmlhttpRequest({
method: 'GET',
url: 'http://localhost:18765/',
onload: () => callback(true),
onerror: () => callback(false)
});
}

let ws;
let sid;
if (window.opener && window.name && window.name.startsWith('ljq_')) {
sid = null;
console.log(log_prefix + `检测到opener，丢弃继承的window.name: ${window.name}`);
window.name = '';
} else {
sid = (window.name && window.name.startsWith('ljq_')) ?
window.name : window.sessionStorage.getItem('ljq_driver_sid');
}
if (!sid) {
sid = `ljq_${Date.now().toString().slice(-2)}${Math.random().toString(36).slice(2, 4)}`;
window.sessionStorage.setItem('ljq_driver_sid', sid);
window.name = sid;
console.log(log_prefix + `创建新会话ID: ${sid}`);
} else {
if (window.name !== sid) window.name = sid;
console.log(log_prefix + `使用现有会话ID: ${sid}`);
}

GM_setValue('sid', sid);

function getIndicator() {
let ind = document.getElementById('ljq-ind');
const dups = document.querySelectorAll('[id="ljq-ind"]');
if (dups.length > 1) {
for (let i = 1; i < dups.length; i++) dups[i].remove();
ind = dups[0];
}
if (!ind && document.body) {
ind = document.createElement('div');
ind.id = 'ljq-ind';
ind.style.cssText = `
position: fixed;bottom: 10px;
right: 10px;background-color: #f44336;
color: white;padding: 8px 12px;
border-radius: 6px;font-size: 14px;
font-weight: bold;z-index: 9999;
transition: background-color 0.3s;
cursor: pointer;box-shadow: 0 3px 6px rgba(0,0,0,0.25);
`;
ind.innerText = log_prefix + '正在连接...';
ind.addEventListener('click', () => alert(`会话ID: ${sid}\n当前URL: ${location.href}`));
document.body.appendChild(ind);
}
return ind;
}

function updateStatus(status, msg) {
if (!document.body) return setTimeout(() => updateStatus(status, msg), 100);
const ind = getIndicator();
if (!ind) return;
if (status === 'ok') {
ind.style.backgroundColor = '#4CAF50';
ind.innerText = log_prefix + '连接成功';
} else if (status === 'disc') {
ind.style.backgroundColor = '#f44336';
ind.innerText = log_prefix + '连接断开';
} else if (status === 'conn') {
ind.style.backgroundColor = '#2196F3';
ind.innerText = log_prefix + '正在连接(HTTP)';
} else if (status === 'err') {
ind.style.backgroundColor = '#FF9800';
ind.innerText = log_prefix + `发生错误 (${msg})`;
} else if (status === 'exec') {
ind.style.backgroundColor = '#2196F3';
ind.innerText = log_prefix + '正在执行指令...';
}
}

function handleError(id, error, errorSource) {
console.error(`${errorSource}错误:`, error);
updateStatus('err', error.message);
const errorMessage = {
type: 'error',
id: id,
sessionId: sid,
error: { name: error.name, message: error.message, stack: error.stack, source: errorSource }
};
if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
ws.send(JSON.stringify(errorMessage));
} else {
GM_xmlhttpRequest({
method: "POST",
url: httpUrl + "api/result",
headers: {"Content-Type": "application/json"},
data: JSON.stringify(errorMessage),
onload: function() {},
onerror: function(err) { console.error("发送错误信息失败", err); }
});
}
}

function smartProcessResult(result) {
if (result === null || result === undefined || typeof result !== 'object') return result;
if (typeof jQuery !== 'undefined' && result instanceof jQuery) {
const elements = [];
for (let i = 0; i < result.length; i++) {
if (result[i] && result[i].nodeType === 1) elements.push(result[i].outerHTML);
}
return elements;
}
if (result instanceof NodeList || result instanceof HTMLCollection) {
const elements = [];
for (let i = 0; i < result.length; i++) {
if (result[i] && result[i].nodeType === 1) elements.push(result[i].outerHTML);
}
return elements;
}
if (result.nodeType === 1) return result.outerHTML;
if (!Array.isArray(result) && typeof result === 'object' && 'length' in result && typeof result.length === 'number') {
const firstElement = result[0];
if (firstElement && firstElement.nodeType === 1) {
const elements = [];
for (let i = 0; i < Math.min(result.length, 100); i++) {
const elem = result[i];
if (elem && elem.nodeType === 1) elements.push(elem.outerHTML);
}
return elements;
}
}
try {
return JSON.parse(JSON.stringify(result, function(key, value) {
if (typeof value === 'object' && value !== null) {
if (value.nodeType === 1) return value.outerHTML;
if (value === window || value === document) return '[Object]';
}
return value;
}));
} catch (e) {
return `[无法序列化的对象: ${e.message}]`;
}
}

if (window.ljq_init) return;
window.ljq_init = true;

function connecthttp() {
if (window.use_ws) return;
updateStatus('conn');
GM_xmlhttpRequest({
method: "POST",
url: httpUrl + "api/longpoll",
headers: {"Content-Type": "application/json"},
data: JSON.stringify({ type: 'ready', url: location.href, sessionId: sid }),
onload: function(resp) {
if (resp.status === 200) {
let data = JSON.parse(resp.responseText);
if (data.id === "" && data.ret === "use ws") return;
if (data.id === "") return setTimeout(connecthttp, 100);
const response = executeCode(data);
if (response.error) {
handleError(data.id, response.error, '执行代码');
} else {
GM_xmlhttpRequest({
method: "POST",
url: httpUrl + "api/result",
headers: {"Content-Type": "application/json"},
data: JSON.stringify({ type: 'result', id: data.id, sessionId: sid, result: response.result })
});
}
} else updateStatus('err', '请求失败');
setTimeout(connecthttp, 1000);
},
onerror: function() { updateStatus('err', '请求失败'); setTimeout(connecthttp, 5000); },
ontimeout: function() { setTimeout(connecthttp, 5000); }
});
}

function executeCode(data) {
let id = data.id || 'unknown';
let result;
if (!data.code) return { error: '没有可执行的代码' };
updateStatus('exec');
const _open = window.open;
window.open = (url, target, features) => { GM_openInTab(url, { active: true }); return { success: true, url: url }; };
try {
const jsCode = data.code.trim();
const lines = jsCode.split(/\r?\n/).filter(l => l.trim());
const lastLine = lines.length > 0 ? lines[lines.length - 1].trim() : '';
if (lastLine.startsWith('return')) {
result = (new Function(jsCode))();
} else {
try { result = eval(jsCode); } catch (e) {
if (e instanceof SyntaxError && /Illegal return statement|return not in function|Illegal 'return' statement/i.test(e.message)) {
result = (new Function(jsCode))();
} else if (e instanceof SyntaxError && /await is only valid in async|await.*async/i.test(e.message)) {
result = (async function() { return eval(jsCode); })();
result = 'Promise is running, cannot get return value. Suggest avoiding await next time, or use global variables (e.g., window.myVar) to store async results.';
} else throw e;
}
}
const processedResult = smartProcessResult(result);
if (result instanceof Promise) {
result.finally(() => window.open = _open);
return { result: processedResult };
}
return { result: processedResult };
} catch (execError) {
return { error: execError };
} finally {
if (!(result instanceof Promise)) setTimeout(() => window.open = _open, 100);
}
}

function connect() {
ws = new WebSocket(wsUrl);
ws.onopen = function() {
window.use_ws = true;
updateStatus('ok');
ws.send(JSON.stringify({ type: 'ready', url: location.href, sessionId: sid }));
};
ws.onclose = function() {
updateStatus('disc');
setTimeout(connect, 5000);
};
ws.onerror = function() {
updateStatus('err', '连接失败');
isWebSocketServerAlive(function(e) { if (e) connecthttp(); });
};
ws.onmessage = async function(e) {
try {
let data = JSON.parse(e.data);
ws.send(JSON.stringify({type: 'ack', id: data.id}));
const response = executeCode(data);
if (response.error) handleError(data.id, response.error, '执行代码');
else {
updateStatus('ok');
ws.send(JSON.stringify({ type: 'result', id: data.id, sessionId: sid, result: response.result }));
}
} catch (parseError) { handleError('unknown', parseError, '解析消息'); }
};
}

function init() {
if (document.body) { getIndicator(); connect(); } else setTimeout(init, 50);
}
const observer = new MutationObserver(() => getIndicator());
if (document.readyState !== 'loading') {
init();
observer.observe(document.body, { childList: true, subtree: true });
} else {
document.addEventListener('DOMContentLoaded', () => {
init();
observer.observe(document.body, { childList: true, subtree: true });
});
}
window.addEventListener('beforeunload', () => {
observer.disconnect();
if (ws && ws.readyState === WebSocket.OPEN) ws.close();
});
})();
