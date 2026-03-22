"""
Playwright 浏览器工具 — 已弃用。
本框架浏览器访问已统一改为篡改猴 + TMWebDriver（与 pc-agent-loop 一致），
见 ga.web_scan / web_execute_js、web_setup_sop。本文件仅保留供无头环境或后续扩展用。
"""
import threading, time, re, json

_lock = threading.Lock()
_browser = None
_context = None
_page = None
_inited = False
_owner_thread = None

MAX_CONTENT_CHARS = 5000
MAX_LINKS = 15


def _ensure_browser():
    """懒初始化 Playwright 浏览器（绑定到调用线程，不可跨线程使用）"""
    global _browser, _context, _page, _inited, _owner_thread
    current_tid = threading.current_thread().ident

    if _inited and _page:
        if _owner_thread != current_tid:
            print(f"[Playwright] Thread changed ({_owner_thread} → {current_tid}), recreating browser")
            _force_close()
        else:
            return _page

    with _lock:
        if _inited and _page and _owner_thread == current_tid:
            return _page
        if _inited:
            _force_close()
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            _browser = pw.chromium.launch(headless=True)
            _context = _browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
            )
            _page = _context.new_page()
            _inited = True
            _owner_thread = current_tid
            print(f"[Playwright] Browser launched (headless Chromium, thread={current_tid})")
            return _page
        except Exception as e:
            print(f"[Playwright] Launch failed: {e}")
            raise


def _force_close():
    """强制关闭现有浏览器实例"""
    global _browser, _context, _page, _inited, _owner_thread
    try:
        if _browser:
            _browser.close()
    except Exception:
        pass
    _browser = _context = _page = None
    _inited = False
    _owner_thread = None


def navigate(url, wait_until="domcontentloaded", timeout=30000):
    """导航到指定 URL，返回页面标题和可交互元素列表"""
    page = _ensure_browser()
    try:
        resp = page.goto(url, wait_until=wait_until, timeout=timeout)
        if resp and resp.status >= 400:
            return {"status": "error", "msg": f"HTTP {resp.status}"}
    except Exception as e:
        return {"status": "error", "msg": f"导航失败: {str(e)[:200]}"}

    time.sleep(1.5)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass
    title = _safe_title(page)
    elements = _extract_interactive_elements(page)
    return {
        "status": "ok",
        "url": page.url,
        "title": title,
        "elements": elements[:MAX_LINKS],
        "element_count": len(elements),
    }


def _safe_title(page):
    """安全获取页面标题，避免导航中的上下文销毁错误"""
    for _ in range(3):
        try:
            return page.title()
        except Exception:
            time.sleep(0.5)
    return "(untitled)"


def click(selector_or_index, timeout=10000):
    """点击页面元素。支持 CSS 选择器或 [n] 格式的元素索引"""
    page = _ensure_browser()
    try:
        if isinstance(selector_or_index, str) and selector_or_index.startswith("[") and selector_or_index.endswith("]"):
            idx = int(selector_or_index[1:-1])
            elements = page.query_selector_all("a, button, [role='button'], input[type='submit'], [onclick]")
            if idx < 0 or idx >= len(elements):
                return {"status": "error", "msg": f"索引 {idx} 超出范围（共 {len(elements)} 个元素）"}
            elements[idx].click(timeout=timeout)
        else:
            page.click(selector_or_index, timeout=timeout)
    except Exception as e:
        return {"status": "error", "msg": f"点击失败: {e}"}

    time.sleep(1.5)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass
    title = _safe_title(page)
    elements = _extract_interactive_elements(page)
    return {
        "status": "ok",
        "url": page.url,
        "title": title,
        "elements": elements[:MAX_LINKS],
    }


def get_content(selector=None):
    """获取当前页面的文本内容（自动去除导航栏等噪音）"""
    page = _ensure_browser()
    try:
        if selector:
            el = page.query_selector(selector)
            if el:
                text = el.inner_text()
            else:
                return {"status": "error", "msg": f"未找到选择器: {selector}"}
        else:
            page.evaluate("""
                document.querySelectorAll('script, style, nav, footer, header, aside, iframe, noscript, [role="navigation"], [role="banner"]')
                    .forEach(el => el.remove());
            """)
            text = page.inner_text("body")

        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
        content = '\n'.join(lines)
        truncated = len(content) > MAX_CONTENT_CHARS
        if truncated:
            content = content[:MAX_CONTENT_CHARS] + "\n...[内容截断，共" + str(len('\n'.join(lines))) + "字符]"

        return {
            "status": "ok",
            "url": page.url,
            "title": _safe_title(page),
            "content": content,
            "truncated": truncated,
            "total_chars": len('\n'.join(lines)),
        }
    except Exception as e:
        return {"status": "error", "msg": f"内容提取失败: {e}"}


def search_google(query):
    """浏览器搜索：优先 Bing，回退 DuckDuckGo（避免 Google 反爬）"""
    page = _ensure_browser()

    from urllib.parse import quote_plus
    encoded_query = quote_plus(query)
    for engine in _SEARCH_ENGINES:
        url = engine["url_template"].format(query=encoded_query)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
        except Exception:
            continue

        try:
            results = page.evaluate(engine["extract_js"])
        except Exception:
            continue
        if results:
            return {"status": "ok", "query": query, "source": engine["name"],
                    "results": results[:8], "count": min(len(results), 8)}

    try:
        results = _fallback_extract_links(page)
    except Exception:
        results = []
    return {
        "status": "ok",
        "query": query,
        "source": "fallback",
        "results": results,
        "count": len(results),
    }


_SEARCH_ENGINES = [
    {
        "name": "bing",
        "url_template": "https://www.bing.com/search?q={query}&ensearch=1",
        "extract_js": """
        () => {
            function decodeBingUrl(href) {
                if (!href || !href.includes('bing.com/ck/a')) return href;
                try {
                    const url = new URL(href);
                    const u = url.searchParams.get('u');
                    if (u && u.startsWith('a1')) {
                        return atob(u.substring(2));
                    }
                } catch(e) {}
                return href;
            }
            const items = [];
            document.querySelectorAll('.b_algo, li.b_algo').forEach(el => {
                const a = el.querySelector('h2 a');
                if (!a) return;
                const snippet = el.querySelector('.b_caption p, .b_algoSlug');
                const rawHref = a.href || '';
                const url = decodeBingUrl(rawHref);
                items.push({
                    title: a.textContent.trim() || '',
                    url: url,
                    snippet: snippet ? snippet.textContent.trim() : ''
                });
            });
            return items;
        }
        """,
    },
    {
        "name": "google",
        "url_template": "https://www.google.com/search?q={query}&hl=en",
        "extract_js": """
        () => {
            const items = [];
            document.querySelectorAll('div.g, div[data-sokoban-container]').forEach(el => {
                const h3 = el.querySelector('h3');
                if (!h3) return;
                const a = el.querySelector('a[href^="http"]');
                const snippet = el.querySelector('[data-sncf], .VwiC3b, .lEBKkf, .IsZvec, .st');
                items.push({
                    title: h3.textContent || '',
                    url: a ? a.href : '',
                    snippet: snippet ? snippet.textContent : ''
                });
            });
            return items.slice(0, 8);
        }
        """,
    },
]


def scroll(direction="down"):
    """滚动页面"""
    page = _ensure_browser()
    delta = 600 if direction == "down" else -600
    page.mouse.wheel(0, delta)
    time.sleep(0.5)
    return {"status": "ok", "direction": direction}


def go_back():
    """浏览器后退"""
    page = _ensure_browser()
    try:
        page.go_back(timeout=10000)
        time.sleep(1)
        return {"status": "ok", "url": page.url, "title": _safe_title(page)}
    except Exception as e:
        return {"status": "error", "msg": f"后退失败: {e}"}


def screenshot(path=None):
    """截图当前页面"""
    page = _ensure_browser()
    import os, base64
    if not path:
        path = os.path.join("temp", f"browser_{int(time.time())}.png")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    page.screenshot(path=path, full_page=False)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {"status": "ok", "path": path, "base64_length": len(b64)}


def close():
    """关闭浏览器"""
    with _lock:
        _force_close()


def _extract_interactive_elements(page):
    """提取页面上的可交互元素（链接、按钮）"""
    try:
        return page.evaluate("""
        () => {
            const els = [];
            document.querySelectorAll('a[href], button, [role="button"], input[type="submit"]').forEach((el, i) => {
                const text = (el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
                if (!text || text.length > 100 || text.length < 1) return;
                const tag = el.tagName.toLowerCase();
                const href = el.getAttribute('href') || '';
                els.push({
                    index: els.length,
                    tag: tag,
                    text: text.substring(0, 80),
                    href: tag === 'a' ? href.substring(0, 200) : undefined
                });
            });
            return els;
        }
        """)
    except Exception:
        return []


def _fallback_extract_links(page):
    """搜索结果提取备用方案"""
    try:
        return page.evaluate("""
        () => {
            const items = [];
            document.querySelectorAll('a').forEach(a => {
                const text = (a.textContent || '').trim();
                const href = a.href || '';
                if (text.length > 15 && text.length < 200 && href.startsWith('http')
                    && !href.includes('google.com/search') && !href.includes('accounts.google')) {
                    items.push({title: text.substring(0, 100), url: href, snippet: ''});
                }
            });
            return items.slice(0, 8);
        }
        """)
    except Exception:
        return []
