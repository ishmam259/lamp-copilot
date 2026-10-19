"""Record the capture scene on a phone (390x844) with the live audit log beside it, as two videos:
python video/record_demo_phone.py <out_dir> -> phone.webm, log.webm, scenes_phone.json (log_offset aligns them)."""
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
    c.innerHTML = window.__phone ? '<div style="width:30px;height:30px;border-radius:50%;background:rgba(20,20,20,.28);border:2px solid rgba(255,255,255,.9);box-shadow:0 0 0 1px rgba(0,0,0,.25)"></div>' : '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M4 2l15 11-6.5 1.2L16 21l-3 1.4-3.4-6.8L4 20z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0px', top:'0px', zIndex:2147483647, pointerEvents:'none', transform: window.__phone ? 'translate(-15px,-15px)' : 'translate(-3px,-2px)', transition:'none'});
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
    click(pg, pg.get_by_role("link", name=label, exact=True).locator("visible=true").last, after)


def scroll(pg, dy, steps=12, ms=60):
    for _ in range(steps):
        pg.mouse.wheel(0, dy / steps); pg.wait_for_timeout(ms)
    pg.wait_for_timeout(500)


def type_slow(pg, loc, text, delay=140):
    click(pg, loc, 200); loc.press_sequentially(text, delay=delay)


def upload(pg, filename, kind="Supplier invoice"):
    click(pg, pg.get_by_role("radio", name=kind).or_(pg.get_by_role("button", name=kind)).first, 600)
    with pg.expect_file_chooser() as fc:
        click(pg, pg.get_by_role("button", name="Take or choose a photo"), 0)
    fc.value.set_files(os.path.join(IMG, filename))



def phone_flow(pg):
    mark("2 capture invoice F")
    nav(pg, "Capture", 1800)
    upload(pg, "invoice_supplier_f.jpg")
    save = pg.get_by_role("button", name="Save to accounts")
    save.wait_for(timeout=60000); hold(pg, 1800)
    scroll(pg, 350); hold(pg, 2200)
    move_to(pg, pg.get_by_text("They match").first, 1500); shot(pg, "p02_invoice_f")
    click(pg, save, 2500)
    mark("2b capture invoice H")
    click(pg, pg.get_by_role("button", name="Capture another"), 1200)
    upload(pg, "invoice_supplier_h.jpg")
    save.wait_for(timeout=60000); hold(pg, 1800); scroll(pg, 350); hold(pg, 1500); shot(pg, "p03_invoice_h")
    click(pg, save, 2500)
    mark("2c capture sales-book page")
    click(pg, pg.get_by_role("button", name="Capture another"), 1200)
    upload(pg, "sales_page.jpg", "Sales book page")
    save.wait_for(timeout=60000); hold(pg, 1500); scroll(pg, 450); hold(pg, 1800); shot(pg, "p04_sales")
    click(pg, save, 2500)
    mark("2d today on the phone")
    nav(pg, "Today", 4500); shot(pg, "p05_today")


LOG_HIDE = "header, nav, [class*=fixed][class*=bottom-0]{visibility:hidden!important}"

with sync_playwright() as p:
    b = p.chromium.launch(args=["--force-color-profile=srgb"])
    httpx.post(f"{API}/dev/reset?with_demo_captures=false", timeout=60)
    dl = os.path.join(OUT, "log"); dp = os.path.join(OUT, "phone")
    lctx = b.new_context(viewport={"width": 760, "height": 1000}, record_video_dir=dl, record_video_size={"width": 760, "height": 1000})
    lctx.add_init_script(CURSOR)
    lg = lctx.new_page(); tl = time.monotonic()
    lg.goto(APP + "/log", wait_until="load")
    lpin = lg.get_by_label("Owner PIN"); lpin.wait_for(timeout=30000); lpin.fill("2468")
    lg.get_by_text("Chain intact").first.wait_for(timeout=30000)
    lg.add_style_tag(content="#__cur{display:none!important}")
    pctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                         record_video_dir=dp, record_video_size={"width": 780, "height": 1688})
    pctx.add_init_script("window.__phone = true;"); pctx.add_init_script(CURSOR)
    pg = pctx.new_page(); T0 = time.monotonic()
    pg.goto(APP + "/", wait_until="load")
    pin = pg.get_by_label("Owner PIN"); pin.wait_for(timeout=30000)
    pg.mouse.move(195, 600); hold(pg, 1000)
    mark("a: unlock with PIN")
    type_slow(pg, pin, "2468", 220); hold(pg, 400)
    pg.get_by_text("Short BDT").first.wait_for(timeout=30000); hold(pg, 2500)
    try:
        phone_flow(pg)
        mark("end"); hold(pg, 1500)
    finally:
        pv, lv = pg.video, lg.video
        pctx.close(); lctx.close()
        shutil.move(pv.path(), os.path.join(OUT, "phone.webm")); shutil.move(lv.path(), os.path.join(OUT, "log.webm"))
    json.dump({"scenes": scenes, "log_offset": round(T0 - tl, 3)}, open(os.path.join(OUT, "scenes_phone.json"), "w"), indent=1)
    b.close()
