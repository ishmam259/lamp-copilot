"""Screen-record the desktop take at 60 fps (needs the screen; FF=path to ffmpeg with ddagrab):
FF=... python video/record_demo_60fps.py <out_dir> b  -> b60.mp4, scenes60_b.json"""
import json, os, re, sys, time, shutil
import httpx
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
APP, API = "http://localhost:3000", "http://127.0.0.1:8000/api/v1"
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "seed", "images")

CURSOR = r"""
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return;
    const c = document.createElement('div'); c.id = '__cur';
    c.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M4 2l15 11-6.5 1.2L16 21l-3 1.4-3.4-6.8L4 20z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0px', top:'0px', zIndex:2147483647, pointerEvents:'none', transform:'translate(-3px,-2px)', transition:'none'});
    const r = document.createElement('div'); r.id = '__ring';
    Object.assign(r.style, {position:'fixed', width:'36px', height:'36px', borderRadius:'50%', border:'3px solid #f5b400', zIndex:2147483646, pointerEvents:'none', opacity:0, transform:'translate(-18px,-18px) scale(.4)', transition:'opacity .35s, transform .35s'});
    document.documentElement.append(c, r);
    const pos = (window.__curpos || {x: 960, y: 540}); c.style.left = pos.x + 'px'; c.style.top = pos.y + 'px';
    addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; window.__curpos = {x: e.clientX, y: e.clientY}; }, true);
    addEventListener('mousedown', e => { r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; r.style.transition = 'none'; r.style.opacity = 1; r.style.transform = 'translate(-18px,-18px) scale(.4)';
      requestAnimationFrame(() => { r.style.transition = 'opacity .45s, transform .45s'; r.style.opacity = 0; r.style.transform = 'translate(-18px,-18px) scale(1.4)'; }); }, true);
    const st = document.createElement('style'); st.textContent = 'nextjs-portal{display:none!important}'; document.head.append(st);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();
"""

scenes, T0 = [], None
mouse = {"x": 960, "y": 540}


def mark(name):
    t = round(time.monotonic() - T0, 2)
    scenes.append({"t": t, "scene": name}); print(f"{t:7.2f}  {name}", flush=True)


def shot(pg, name):
    pg.screenshot(path=os.path.join(OUT, name + ".png"))


def hold(pg, ms):
    pg.wait_for_timeout(ms)


def move_to(pg, loc, settle=350):
    loc.scroll_into_view_if_needed(); pg.wait_for_timeout(250)
    bb = loc.bounding_box()
    x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
    pg.mouse.move(x, y, steps=28); mouse.update(x=x, y=y)
    pg.wait_for_timeout(settle)


def click(pg, loc, after=900):
    try:
        loc.wait_for(state="visible", timeout=30000)
    except Exception:
        pg.screenshot(path=os.path.join(OUT, "FAIL.png")); raise
    move_to(pg, loc)
    pg.mouse.down(); pg.wait_for_timeout(90); pg.mouse.up()
    pg.wait_for_timeout(after)


def nav(pg, label, after=2200):
    click(pg, pg.locator("aside, nav").get_by_role("link", name=re.compile("^" + re.escape(label))).first, after)


def scroll(pg, dy, steps=12, ms=60):
    pg.evaluate("""([x, y, dy]) => {
      let el = document.elementFromPoint(x, y);
      while (el && el !== document.body && el !== document.documentElement) {
        const s = getComputedStyle(el);
        if (/(auto|scroll)/.test(s.overflowY) && el.scrollHeight > el.clientHeight + 2) break;
        el = el.parentElement;
      }
      const t = (el && el !== document.body && el !== document.documentElement) ? el : window;
      t.scrollBy({top: dy, behavior: 'smooth'});
    }""", [900, 600, dy])
    pg.wait_for_timeout(1300)


def type_slow(pg, loc, text, delay=140):
    click(pg, loc, 200); loc.press_sequentially(text, delay=delay)


def upload(pg, filename, kind="Supplier invoice"):
    click(pg, pg.get_by_role("radio", name=kind).or_(pg.get_by_role("button", name=kind)).first, 600)
    with pg.expect_file_chooser() as fc:
        click(pg, pg.get_by_role("button", name="Take or choose a photo"), 0)
    fc.value.set_files(os.path.join(IMG, filename))


def take_a(pg):
    # 2. Capture: two invoices and a sales-book page
    mark("2 capture invoice F")
    nav(pg, "Capture")
    upload(pg, "invoice_supplier_f.jpg")
    save = pg.get_by_role("button", name="Save to accounts")
    save.wait_for(timeout=60000); hold(pg, 1500)
    move_to(pg, pg.get_by_text("They match").first, 1800); shot(pg, "c02_invoice_f")
    click(pg, save, 2500)
    mark("2b capture invoice H")
    click(pg, pg.get_by_role("button", name="Capture another"), 1200)
    upload(pg, "invoice_supplier_h.jpg")
    save.wait_for(timeout=60000); hold(pg, 2500); shot(pg, "c03_invoice_h")
    click(pg, save, 2500)
    mark("2c capture sales-book page")
    click(pg, pg.get_by_role("button", name="Capture another"), 1200)
    upload(pg, "sales_page.jpg", "Sales book page")
    save.wait_for(timeout=60000); hold(pg, 1500); scroll(pg, 400); hold(pg, 1500); shot(pg, "c04_sales")
    click(pg, save, 3000)


def take_b(pg):
    mark("3 today with books")
    nav(pg, "Today", 4500); shot(pg, "c05_today")
    scroll(pg, 650); hold(pg, 3500); scroll(pg, -650)
    mark("3b cash")
    nav(pg, "Cash", 4000); scroll(pg, 500); hold(pg, 3000); shot(pg, "c06_cash")
    mark("3c stock")
    nav(pg, "Stock", 3500); shot(pg, "c07_stock"); hold(pg, 3000)
    mark("4 ask LaMP")
    click(pg, pg.get_by_role("button", name="Ask LaMP"), 1500)
    click(pg, pg.get_by_role("button", name="Can I pay Supplier A's order next week?"), 1000)
    try:
        pg.get_by_text("money figures traced").first.wait_for(timeout=40000)
    except Exception:
        shot(pg, "FAIL_chat"); raise
    hold(pg, 1500)
    shot(pg, "c09_chat")
    hold(pg, 12000); shot(pg, "c10_chat_end")
    pg.keyboard.press("Escape"); hold(pg, 1200)
    mark("4a return claim")
    nav(pg, "Stock", 3000)
    click(pg, pg.get_by_role("button", name="Draft return claims for BDT 9,200"), 2500)
    mark("4b funding plan")
    nav(pg, "Funding", 4000); shot(pg, "c11_funding")
    scroll(pg, 350); hold(pg, 3500)
    mark("4c approve return, trim and extension")
    nav(pg, "Actions", 3000); shot(pg, "c12_actions_plan")
    for _ in range(3):
        card = pg.locator("li").filter(has=pg.get_by_role("button", name="Approve", exact=True)).filter(has_not_text="needs your PIN")
        if card.count() == 0: break
        click(pg, card.first.get_by_role("button", name="Approve", exact=True), 3200)
    shot(pg, "c13_actions_after")

    # 5. Supplier declines, passport, loan, lender
    mark("5 supplier declines, backup loan raised")
    acts = pg.evaluate("""async () => (await fetch('/api/v1/pharmacies/green-life/actions', {credentials: 'include'})).json()""")
    ext = next(a for a in acts if a["kind"] == "extension_request")
    hold(pg, 1500)
    r = httpx.post(f"{API}/dev/simulate/supplier-reply", json={"action_id": ext["id"], "accepted": False}, timeout=30)
    print("supplier reply", r.status_code, r.text[:200])
    hold(pg, 5000); shot(pg, "c14_declined")
    pg.reload(wait_until="load"); hold(pg, 4000); shot(pg, "c15_actions_loan")
    mark("5b passport and sharing")
    nav(pg, "Passport", 4000); shot(pg, "c16_passport")
    scroll(pg, 400); hold(pg, 2500)
    click(pg, pg.get_by_role("switch", name="Share passport with Wallet Lender"), 3000); shot(pg, "c17_sharing")
    mark("5c approve loan with PIN")
    nav(pg, "Actions", 3000)
    click(pg, pg.locator("li").filter(has_text="needs your PIN").first.get_by_role("button", name="Approve", exact=True), 1500)
    dpin = pg.get_by_role("dialog").locator("input").first
    type_slow(pg, dpin, "2468", 220); hold(pg, 300)
    if dpin.is_visible(): dpin.press("Enter")
    hold(pg, 4000); shot(pg, "c18_loan_approved")
    mark("5d lender view")
    nav(pg, "Lender view", 4000); shot(pg, "c19_lender")
    click(pg, pg.get_by_role("button", name="Decide", exact=True), 4500); shot(pg, "c20_payout")
    scroll(pg, 400); hold(pg, 3000)

    # 6. Injection
    mark("6 injection invoice")
    nav(pg, "Capture", 2000)
    upload(pg, "injection_invoice.jpg")
    hold(pg, 9000); shot(pg, "c21_injection")
    scroll(pg, 400); hold(pg, 4000); shot(pg, "c22_injection2")
    nav(pg, "Actions", 4000); shot(pg, "c23_actions_after_inj")
    mark("6b audit log")
    nav(pg, "Audit log", 5000); shot(pg, "c24_log")
    scroll(pg, 600); hold(pg, 3000)
    mark("end")
    hold(pg, 1500)


FF = os.environ["FF"]


def run_take(b, name, captures, flow):
    global T0
    import subprocess
    httpx.post(f"{API}/dev/reset?with_demo_captures={'true' if captures else 'false'}", timeout=60)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080})
    ctx.add_init_script(CURSOR)
    ctx.add_init_script("try{Object.defineProperty(Notification,'permission',{get:()=>'denied'})}catch(e){}")
    pg = ctx.new_page()
    cdp = ctx.new_cdp_session(pg)
    wid = cdp.send("Browser.getWindowForTarget")["windowId"]
    cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "fullscreen"}})
    pg.goto(APP + "/", wait_until="load")
    pin = pg.get_by_label("Owner PIN"); pin.wait_for(timeout=30000)
    pg.mouse.move(960, 700); hold(pg, 2500)
    out = os.path.join(OUT, name + "60.mp4")
    ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "ddagrab=output_idx=0:framerate=60:draw_mouse=0",
                           "-vf", "hwdownload,format=bgra,crop=1920:1080:0:0,format=yuv420p", "-c:v", "h264_nvenc", "-preset", "p6",
                           "-tune", "hq", "-rc", "vbr", "-cq", "16", "-b:v", "0", "-r", "60", out], stdin=subprocess.PIPE)
    time.sleep(1.0); T0 = time.monotonic()
    hold(pg, 1000)
    mark(f"{name}: unlock with PIN")
    type_slow(pg, pin, "2468", 220); hold(pg, 400)
    if pin.is_visible(): pin.press("Enter")
    pg.get_by_text("Short BDT").first.wait_for(timeout=30000); hold(pg, 2500)
    try:
        flow(pg)
    finally:
        ff.communicate(b"q", timeout=60)
        ctx.close()


with sync_playwright() as p:
    b = p.chromium.launch(headless=False, args=["--force-device-scale-factor=1", "--window-position=0,0", "--hide-scrollbars", "--disable-infobars"],
                          ignore_default_args=["--enable-automation"])
    for t in sys.argv[2:] or ["b"]:
        scenes.clear()
        run_take(b, t, t == "b", take_a if t == "a" else take_b)
        json.dump(scenes, open(os.path.join(OUT, f"scenes60_{t}.json"), "w"), indent=1)
    b.close()
