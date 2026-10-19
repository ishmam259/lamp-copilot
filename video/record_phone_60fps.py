"""Screen-record the capture scene at 60 fps: the phone layout and the live audit log in video/phone_composite/index.html.
FF=... SITE=video/phone_composite python video/record_phone_60fps.py <out_dir>  -> a60.mp4, scenes60_a.json"""
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
    if (window.name !== 'phone') { const st0 = document.createElement('style'); st0.textContent = 'nextjs-portal{display:none!important}'; document.head.append(st0); return; }
    window.__phone = true;
    if (document.getElementById('__cur')) return;
    const c = document.createElement('div'); c.id = '__cur';
    c.innerHTML = '<div style="width:30px;height:30px;border-radius:50%;background:rgba(20,20,20,.28);border:2px solid rgba(255,255,255,.9);box-shadow:0 0 0 1px rgba(0,0,0,.25)"></div>';
    Object.assign(c.style, {position:'fixed', left:'0px', top:'0px', zIndex:2147483647, pointerEvents:'none', transform:'translate(-15px,-15px)', transition:'none'});
    const r = document.createElement('div'); r.id = '__ring';
    Object.assign(r.style, {position:'fixed', width:'36px', height:'36px', borderRadius:'50%', border:'3px solid #f5b400', zIndex:2147483646, pointerEvents:'none', opacity:0, transform:'translate(-18px,-18px) scale(.4)', transition:'opacity .35s, transform .35s'});
    document.documentElement.append(c, r);
    const pos = (window.__curpos || {x: 960, y: 540}); c.style.left = pos.x + 'px'; c.style.top = pos.y + 'px';
    addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; window.__curpos = {x: e.clientX, y: e.clientY}; }, true);
    addEventListener('mousedown', e => { r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; r.style.transition = 'none'; r.style.opacity = 1; r.style.transform = 'translate(-18px,-18px) scale(.4)';
      requestAnimationFrame(() => { r.style.transition = 'opacity .45s, transform .45s'; r.style.opacity = 0; r.style.transform = 'translate(-18px,-18px) scale(1.4)'; }); }, true);
    const st = document.createElement('style'); st.textContent = 'nextjs-portal{display:none!important} html{zoom:1.1846}'; document.head.append(st);
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



ZOOM = 1.1846


def pscroll(pg, dy):
    pg.frame(name="phone").evaluate("""([x, y, dy]) => {
      let el = document.elementFromPoint(x, y);
      while (el && el !== document.body && el !== document.documentElement) {
        const s = getComputedStyle(el);
        if (/(auto|scroll)/.test(s.overflowY) && el.scrollHeight > el.clientHeight + 2) break;
        el = el.parentElement;
      }
      const t = (el && el !== document.body && el !== document.documentElement) ? el : window;
      t.scrollBy({top: dy, behavior: 'smooth'});
    }""", [150, 300, dy])
    pg.wait_for_timeout(1300)


def pupload(pg, F, filename, kind="Supplier invoice"):
    click(pg, F.get_by_role("radio", name=kind).or_(F.get_by_role("button", name=kind)).first, 600)
    with pg.expect_file_chooser() as fc:
        click(pg, F.get_by_role("button", name="Take or choose a photo"), 0)
    fc.value.set_files(os.path.join(IMG, filename))


def pnav(pg, F, label, after=2200):
    click(pg, F.get_by_role("link", name=label, exact=True).locator("visible=true").last, after)


def phone_flow(pg, F):
    mark("2 capture invoice F")
    pnav(pg, F, "Capture", 1800)
    pupload(pg, F, "invoice_supplier_f.jpg")
    save = F.get_by_role("button", name="Save to accounts")
    save.wait_for(timeout=60000); hold(pg, 1800)
    pscroll(pg, 300); hold(pg, 1800)
    move_to(pg, F.get_by_text("They match").first, 1500); shot(pg, "q02_invoice_f")
    click(pg, save, 2500)
    mark("2b capture invoice H")
    click(pg, F.get_by_role("button", name="Capture another"), 1200)
    pupload(pg, F, "invoice_supplier_h.jpg")
    save.wait_for(timeout=60000); hold(pg, 1800); pscroll(pg, 300); hold(pg, 1200); shot(pg, "q03_invoice_h")
    click(pg, save, 2500)
    mark("2c capture sales-book page")
    click(pg, F.get_by_role("button", name="Capture another"), 1200)
    pupload(pg, F, "sales_page.jpg", "Sales book page")
    save.wait_for(timeout=60000); hold(pg, 1500); pscroll(pg, 400); hold(pg, 1500); shot(pg, "q04_sales")
    click(pg, save, 2500)
    mark("2d today on the phone")
    pnav(pg, F, "Today", 4500); shot(pg, "q05_today")


TEST = os.environ.get("TEST") == "1"
FF = os.environ.get("FF", "")
import subprocess
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", os.environ["SITE"]],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    with sync_playwright() as p:
        args = ["--force-device-scale-factor=1", "--window-position=0,0", "--hide-scrollbars", "--disable-infobars"]
        b = p.chromium.launch(headless=TEST, args=args, ignore_default_args=["--enable-automation"])
        time.sleep(1)
        httpx.post(f"{API}/dev/reset?with_demo_captures=false", timeout=60)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        ctx.add_init_script(CURSOR)
        ctx.add_init_script("try{Object.defineProperty(Notification,'permission',{get:()=>'denied'})}catch(e){}")
        pg = ctx.new_page()
        if not TEST:
            cdp = ctx.new_cdp_session(pg)
            wid = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "fullscreen"}})
        pg.goto("http://localhost:8765/", wait_until="load")
        F = pg.frame_locator("#phone")
        pin = F.get_by_label("Owner PIN"); pin.wait_for(timeout=30000)
        pg.evaluate("document.getElementById('log').src = 'http://localhost:3000/log'")
        L = pg.frame_locator("#log")
        lpin = L.get_by_label("Owner PIN"); lpin.wait_for(timeout=30000); lpin.fill("2468")
        L.get_by_text("Chain intact").first.wait_for(timeout=30000)
        pg.mouse.move(590, 650); mouse.update(x=590, y=650); hold(pg, 2500)
        shot(pg, "q00_start")
        ff = None
        if not TEST:
            ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "ddagrab=output_idx=0:framerate=60:draw_mouse=0",
                                   "-vf", "hwdownload,format=bgra,crop=1920:1080:0:0,format=yuv420p", "-c:v", "h264_nvenc", "-preset", "p6",
                                   "-tune", "hq", "-rc", "vbr", "-cq", "16", "-b:v", "0", "-r", "60", os.path.join(OUT, "a60.mp4")], stdin=subprocess.PIPE)
            time.sleep(1.0)
        T0 = time.monotonic(); hold(pg, 1000)
        mark("a: unlock with PIN")
        type_slow(pg, pin, "2468", 220); hold(pg, 400)
        F.get_by_text("Short BDT").first.wait_for(timeout=30000); hold(pg, 2500); shot(pg, "q01_today")
        try:
            phone_flow(pg, F)
            mark("end"); hold(pg, 1500)
        finally:
            if ff: ff.communicate(b"q", timeout=60)
            json.dump(scenes, open(os.path.join(OUT, "scenes60_a.json"), "w"), indent=1)
            ctx.close(); b.close()
finally:
    srv.terminate()
