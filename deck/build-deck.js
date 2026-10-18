// Builds deck/LaMP-Copilot.pptx. Run from deck/: node build-deck.js
// Visual language follows our BCOLBD deck: photo statement slides, "▶ SECTION" headings,
// problem slides with a dashed core-issue box and symptom icons, green step panels with
// cut-out people, dense infographic slides with green-header tables. Fonts: Poppins.
// Every number must match docs/PLAN.md section 6 (golden numbers).
// The talk script lives in SPEAKER_NOTES.md, not in the slides.
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const L = require("react-icons/lu");
const { applyTheme } = require("./apply_theme.js");

// ---------- palette (from BCOLBD) ----------
const K = {
  ink: "231F20", white: "FFFFFF", grey: "5A5A5A", mute: "8A8A8A", line: "D9D9D9",
  deep: "0F5132", mid: "198754", title: "2A7651", bright: "00BF63", lime: "6EF06E", strip: "00D300",
  mint: "E9F7EE", red: "BD0000", red2: "EA383A", redSoft: "F04A4A", redTint: "FDF0F0",
  hi: "FF4B4B", blue: "5B9BD5", blueTint: "EEF5FC", yellow: "FFD400",
};
const THEME = {
  name: "LaMP BCOLBD",
  headFontFace: "Poppins",
  bodyFontFace: "Poppins",
  colors: {
    dk1: K.ink, lt1: K.white, dk2: K.deep, lt2: K.mint, accent1: K.bright, accent2: K.mid,
    accent3: K.red, accent4: K.lime, accent5: K.title, accent6: K.grey, hlink: K.mid, folHlink: K.deep,
  },
};
const F = { reg: "Poppins", light: "Poppins Light", med: "Poppins Medium", semi: "Poppins SemiBold", xbold: "Poppins ExtraBold" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.title = "LaMP-Copilot";
pres.subject = "FinTechathon 2026, International Track, Topic E: SME Finance Copilot";
pres.author = "Team LaMP";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

const W = 13.333, H = 7.5, M = 0.55;
const A = (f) => path.join(__dirname, "assets", f);

pres.defineSlideMaster({ title: "PLAIN", background: { color: K.white }, objects: [], slideNumber: { x: 12.55, y: 7.08, w: 0.5, h: 0.25, fontFace: F.reg, fontSize: 8, color: "9A9A9A", align: "right" } });
pres.defineSlideMaster({ title: "BLANK", background: { color: K.white }, objects: [] });
pres.defineSlideMaster({ title: "RED", background: { color: K.red }, objects: [] });

// ---------- helpers ----------
function T(s, text, o) {
  s.addText(text, { fontFace: F.reg, color: K.ink, margin: 0, valign: "top", isTextBox: true, ...o });
}
async function icon(Comp, hex, px = 256) {
  const svg = renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: px }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}
async function size(f) {
  const m = await sharp(A(f)).metadata();
  return { w: m.width, h: m.height };
}
async function fit(s, f, x, y, w, h, align = "center", valign = "middle") {
  const { w: pw, h: ph } = await size(f);
  let iw = w, ih = (w * ph) / pw;
  if (ih > h) { ih = h; iw = (h * pw) / ph; }
  const ix = align === "left" ? x : align === "right" ? x + w - iw : x + (w - iw) / 2;
  const iy = valign === "top" ? y : valign === "bottom" ? y + h - ih : y + (h - ih) / 2;
  s.addImage({ path: A(f), x: ix, y: iy, w: iw, h: ih });
  return { x: ix, y: iy, w: iw, h: ih };
}
function cover(s, f, x, y, w, h) {
  s.addImage({ path: A(f), x, y, w, h, sizing: { type: "cover", w, h } });
}
function rect(s, x, y, w, h, fill, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill, transparency: o.t || 0 }, line: o.line ? o.line : { color: fill, width: 0, transparency: o.t || 0 } });
}
function rrect(s, x, y, w, h, fill, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: o.r ?? 0.08, fill: fill ? { color: fill } : { type: "none" }, line: o.line ? o.line : { color: fill || K.white, width: 0 } });
}
function tri(s, x, y, sz = 0.2, color = K.bright) {
  s.addShape(pres.shapes.ISOSCELES_TRIANGLE, { x, y, w: sz, h: sz * 0.9, rotate: 90, fill: { color }, line: { color, width: 0 } });
}
function strip(s) {
  rect(s, 0, H - 0.12, W, 0.12, K.strip);
}
// "▶ SITUATION ANALYSIS" (two-tone like BCOLBD)
function head(s, a, b = "", o = {}) {
  const y = o.y ?? 0.42, color = o.color ?? K.ink;
  tri(s, M, y + 0.1, 0.2, K.bright);
  const runs = [{ text: a, options: { fontFace: F.semi, color } }];
  if (b) runs.push({ text: " " + b, options: { fontFace: o.bLight ? F.reg : F.semi, color: o.bColor ?? color } });
  T(s, runs, { x: M + 0.32, y, w: o.w ?? 11.5, h: 0.42, fontSize: o.size ?? 20, valign: "middle" });
}
// dense-slide heading: ▶ TITLE ———— LaMP
function ruleHead(s, title, o = {}) {
  head(s, title, "", { size: 20 });
  const end = M + 0.32 + title.length * (o.cw ?? 0.188) + 0.25;
  s.addShape(pres.shapes.LINE, { x: end, y: 0.63, w: 12.2 - end, h: 0, line: { color: K.line, width: 0.75 } });
  T(s, "LaMP", { x: 12.25, y: 0.53, w: 0.55, h: 0.22, fontSize: 8, fontFace: F.semi, color: "B5B5B5", align: "right" });
}
// mint row with a green left bar (BCOLBD's signature card)
function barRow(s, x, y, w, h, text, o = {}) {
  rect(s, x, y, w, h, o.fill ?? K.mint);
  rect(s, x, y, 0.06, h, o.bar ?? K.bright);
  T(s, text, { x: x + 0.2, y: y + 0.04, w: w - 0.3, h: h - 0.08, fontSize: o.size ?? 11.5, valign: o.valign ?? "middle", color: o.color ?? K.ink, fontFace: o.font ?? F.reg });
}
function banner(s, x, y, w, h, text, fill = K.deep, o = {}) {
  rrect(s, x, y, w, h, fill, { r: 0.05 });
  T(s, text, { x: x + 0.25, y, w: w - 0.5, h, fontSize: o.size ?? 12, color: K.white, align: o.align ?? "center", valign: "middle", fontFace: o.font ?? F.med });
}
function tableHead(cells, fill = K.mid) {
  return cells.map((t) => ({ text: t, options: { fontFace: F.semi, color: K.white, fill: { color: fill }, fontSize: 10.5, valign: "middle", align: "left" } }));
}
function cell(t, o = {}) {
  return { text: t, options: { fontFace: o.font ?? F.reg, fontSize: o.size ?? 10.5, color: o.color ?? K.ink, fill: { color: o.fill ?? K.white }, valign: "middle", align: o.align ?? "left" } };
}
async function limeIcon(s, x, y, d, file) {
  rrect(s, x, y, d, d, "5FE35F", { r: 0.18 });
  await fit(s, file, x + d * 0.17, y + d * 0.17, d * 0.66, d * 0.66);
}
async function circleIcon(s, x, y, d, Comp, color = K.bright) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: K.white }, line: { color, width: 1.5 } });
  s.addImage({ data: await icon(Comp, color), x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52 });
}

// ---------- slides ----------
async function build() {
  // 1. Title
  pres.addSection({ title: "Opening" });
  {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Opening" });
    cover(s, "pharmacy.jpg", 0, 0, W, H);
    rect(s, 0, 0, W, H, "000000", { t: 42 });
    await fit(s, "bc/logo.png", W / 2 - 0.75, 0.55, 1.5, 1.5);
    T(s, [
      { text: "LaMP", options: { color: K.bright } },
      { text: "-Copilot", options: { color: K.white } },
    ], { x: 0.5, y: 2.15, w: W - 1, h: 1.1, fontSize: 60, fontFace: F.xbold, align: "center" });
    T(s, "An AI finance officer for neighbourhood pharmacies in Bangladesh", { x: 0.8, y: 3.3, w: W - 1.6, h: 0.55, fontSize: 24, fontFace: F.med, color: K.white, align: "center" });
    T(s, "Real accounts from paper records, early warning of cash trouble, and the cheapest way to fund every order.", {
      x: 2.0, y: 3.95, w: W - 4.0, h: 0.85, fontSize: 15, fontFace: F.light, color: "EDEDED", align: "center",
    });
    rrect(s, W / 2 - 4.4, 5.25, 8.8, 0.5, K.bright, { r: 0.5 });
    T(s, "FINTECHATHON 2026  ·  INTERNATIONAL TRACK  ·  TOPIC E: SME FINANCE COPILOT", { x: W / 2 - 4.4, y: 5.25, w: 8.8, h: 0.5, fontSize: 12.5, fontFace: F.semi, color: K.white, align: "center", valign: "middle", charSpacing: 1 });
    T(s, "Team LaMP  ·  Ishmam Tahmid (team lead)  ·  Farhan Tahsin Khan", { x: 0.8, y: 6.15, w: W - 1.6, h: 0.4, fontSize: 13, fontFace: F.reg, color: K.white, align: "center" });
  }

  // 2. Hook statement
  {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Opening" });
    cover(s, "counter.jpg", 0, 0, W, H);
    rect(s, 0, 0, W, H, "000000", { t: 38 });
    T(s, [
      { text: "Last month, Green Life Pharmacy in Bogura sold " },
      { text: "BDT 412,500", options: { color: K.hi } },
      { text: " of medicine and kept only " },
      { text: "BDT 13,500", options: { color: K.hi } },
      { text: ". The owner couldn't see it: every number lived in a " },
      { text: "stack of paper", options: { color: K.hi } },
      { text: "." },
    ], { x: 1.4, y: 1.7, w: W - 2.8, h: 3.6, fontSize: 32, fontFace: F.xbold, color: K.white, align: "center", valign: "middle", lineSpacingMultiple: 1.05 });
  }

  // 3. Situation analysis
  pres.addSection({ title: "Problem" });
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Problem" });
    head(s, "SITUATION ANALYSIS");
    // left: the manufacturing triumph
    const lx = M, lw = 5.75;
    T(s, "The Manufacturing Triumph:", { x: lx, y: 1.05, w: lw, h: 0.35, fontSize: 15, fontFace: F.med });
    rect(s, lx, 1.48, lw, 0.34, "1FA463");
    T(s, "PHARMACEUTICAL MARKET", { x: lx, y: 1.48, w: lw, h: 0.34, fontSize: 10.5, fontFace: F.semi, color: K.white, align: "center", valign: "middle", charSpacing: 1 });
    s.addImage({ path: A("bc/greenbox.png"), x: lx, y: 1.82, w: lw, h: 1.75, sizing: { type: "cover", w: lw, h: 1.75 } });
    await fit(s, "bc/map-faint.png", lx + lw / 2 - 0.9, 1.86, 1.8, 1.65);
    T(s, [{ text: "$ 3.3 Billion", options: { fontSize: 24, fontFace: F.semi, breakLine: true } }, { text: "market size, MAT Q1 2026", options: { fontSize: 11 } }], { x: lx + 0.3, y: 1.98, w: 2.9, h: 0.8 });
    T(s, [{ text: "~11%", options: { fontSize: 24, fontFace: F.semi, breakLine: true } }, { text: "4-year growth (CAGR)", options: { fontSize: 11 } }], { x: lx + 3.4, y: 1.98, w: 2.2, h: 0.8 });
    T(s, [{ text: "1.83%+  ", options: { fontSize: 18, fontFace: F.semi } }, { text: "of GDP", options: { fontSize: 13, fontFace: F.med } }], { x: lx + 0.3, y: 2.95, w: lw - 0.6, h: 0.45, align: "center" });
    await fit(s, "bc/donut.png", lx, 3.8, 1.05, 1.05);
    T(s, "98% of Demand Met Locally", { x: lx + 1.25, y: 3.78, w: lw - 1.25, h: 0.36, fontSize: 15, fontFace: F.semi });
    T(s, "About 213 working manufacturers make nearly all the medicine. Supply isn't the bottleneck; paying for it at the last mile is.", { x: lx + 1.25, y: 4.14, w: lw - 1.25, h: 0.8, fontSize: 11 });
    barRow(s, lx, 5.1, lw, 0.95, "Credit flows informally and invisibly between makers and shops, at a cost no one measures.", { size: 12.5 });
    // right: last-mile reality
    const rx = 6.75, rw = W - M - rx;
    T(s, "The Last-Mile Retail Reality:", { x: rx, y: 1.05, w: rw, h: 0.35, fontSize: 15, fontFace: F.med });
    const rows = [
      ["bc/shop.png", "173,500+ Licensed Pharmacies", "Plus up to 100,000 unlicensed shops, mostly small and owner-run."],
      ["bc/handcash.png", "Thin 10–15% Margins", "Chemists are publicly demanding a higher commission from drug makers."],
      ["bc/credit.png", "Forced Credit Dependency", "Paper invoices and supplier credit from 10–50 drug companies each."],
      ["bc/warnsearch.png", "Expiry and Patient Credit", "Unsold stock expires as pure loss; patients buy on credit too."],
    ];
    for (let i = 0; i < rows.length; i++) {
      const y = 1.48 + i * 0.98;
      rect(s, rx, y, rw, 0.88, K.mint);
      await fit(s, rows[i][0], rx + 0.15, y + 0.14, 0.6, 0.6);
      T(s, rows[i][1], { x: rx + 0.95, y: y + 0.08, w: rw - 1.05, h: 0.3, fontSize: 13, fontFace: F.semi });
      T(s, rows[i][2], { x: rx + 0.95, y: y + 0.4, w: rw - 1.05, h: 0.44, fontSize: 11.5 });
    }
    rect(s, 1.35, 6.2, W - 2.7, 0.62, K.red2);
    T(s, "THE LAST MILE RUNS A MULTI-SUPPLIER CREDIT BUSINESS ON PAPER, WITH NO VIEW OF CASH, EXPIRY OR BORROWING COST", {
      x: 1.5, y: 6.2, w: W - 3.0, h: 0.62, fontSize: 11, fontFace: F.med, color: K.white, align: "center", valign: "middle",
    });
    T(s, "Sources: IQVIA MAT Q1 2026 (via industry reports); BAPI; DGDA (via Financial Express, Innovision); Springer; UNB.", {
      x: M, y: 6.9, w: 11.9, h: 0.3, fontSize: 7.5, color: K.mute,
    });
  }

  // 4. Meet Green Life
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Problem" });
    ruleHead(s, "MEET GREEN LIFE PHARMACY, BOGURA");
    rrect(s, M, 0.95, W - 2 * M, 0.5, null, { line: { color: K.bright, width: 1 }, r: 0.06 });
    T(s, [
      { text: "The shop behind every number in this deck. ", options: { fontFace: F.semi } },
      { text: "Illustrative but consistent; our engines and tests reproduce each figure exactly." },
    ], { x: M + 0.2, y: 0.95, w: W - 2 * M - 0.4, h: 0.5, fontSize: 11, valign: "middle" });
    const tw = 6.15;
    T(s, "Last 30 Days: Profit and Loss", { x: M, y: 1.65, w: tw, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    s.addTable([
      tableHead(["Line", "BDT", "What it means"]),
      [cell("Sales"), cell("412,500", { align: "right" }), cell("From the sales book")],
      [cell("Gross profit at a 12% margin"), cell("49,500", { align: "right" }), cell("After the cost of medicine")],
      [cell("Rent, salaries, utilities"), cell("– 36,000", { align: "right" }), cell("Fixed overheads")],
      [cell("Net profit", { font: F.semi, fill: K.mint }), cell("13,500", { font: F.semi, fill: K.mint, align: "right" }), cell("What the owner keeps", { fill: K.mint })],
    ], { x: M, y: 1.98, w: tw, colW: [2.25, 0.95, 2.95], rowH: 0.34, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    T(s, "Working Capital Snapshot", { x: M, y: 3.85, w: tw, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    s.addTable([
      tableHead(["Item", "Value", "Read as"]),
      [cell("Stock on shelves"), cell("BDT 210,000", { align: "right" }), cell("17.4 days of purchases")],
      [cell("Owed by patients"), cell("BDT 38,000", { align: "right" }), cell("2.8 days of sales")],
      [cell("Active suppliers"), cell("23", { align: "right" }), cell("23 sets of dues to track")],
      [cell("Supplier invoices, 3 months"), cell("41", { align: "right" }), cell("38 paid on time")],
    ], { x: M, y: 4.18, w: tw, colW: [2.25, 1.25, 2.65], rowH: 0.34, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    // right: tiles
    const rx = 7.0, tw2 = (W - M - rx - 0.2) / 2;
    const tiles = [
      ["BDT 18,400", "of stock expires within 60 days", "6 batches"],
      ["BDT 9,200", "can still go back to suppliers", "68% of a month's profit"],
      ["BDT 60,000", "Supplier A stock-up order", "due Mon 26 Oct"],
      ["BDT 41,000", "forecast cash on that day", "short BDT 19,000"],
    ];
    tiles.forEach(([b, t, n], i) => {
      const x = rx + (i % 2) * (tw2 + 0.2), y = 1.65 + Math.floor(i / 2) * 1.55;
      rrect(s, x, y, tw2, 1.38, K.white, { line: { color: i === 3 ? K.red2 : K.bright, width: 1.25 }, r: 0.06 });
      T(s, b, { x, y: y + 0.12, w: tw2, h: 0.55, fontSize: 24, fontFace: F.semi, color: i === 3 ? K.red : K.mid, align: "center" });
      T(s, t, { x: x + 0.1, y: y + 0.68, w: tw2 - 0.2, h: 0.3, fontSize: 10.5, align: "center" });
      T(s, n, { x: x + 0.1, y: y + 0.97, w: tw2 - 0.2, h: 0.28, fontSize: 9.5, color: K.grey, align: "center", fontFace: F.med });
    });
    banner(s, rx, 4.83, W - M - rx, 1.05, "One expired batch or one unnecessary loan can wipe out a week of profit.", K.deep, { size: 12 });
    barRow(s, M, 6.15, W - 2 * M, 0.72, "All of it lives in 41 paper invoices and a handwritten sales book, so not even the owner can see it.", { size: 11.5 });
    strip(s);
  }

  // 5 & 6. Problem identification
  const problem = async (who, photo, coreBody, symptoms) => {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Problem" });
    const pw = 6.95;
    cover(s, photo, 0, 0, pw, H);
    rect(s, 0, 0, pw, H, "000000", { t: 45 });
    s.addImage({ path: A("bc/grad-grey.png"), x: pw, y: 0, w: W - pw, h: H, sizing: { type: "cover", w: W - pw, h: H } });
    tri(s, M, 0.52, 0.2, K.bright);
    T(s, [{ text: "PROBLEM", options: { fontFace: F.semi } }, { text: " IDENTIFICATION", options: { fontFace: F.reg } }], { x: M + 0.32, y: 0.42, w: 5.9, h: 0.42, fontSize: 20, color: K.white, valign: "middle" });
    T(s, `(${who})`, { x: pw + 0.3, y: 0.42, w: 5.8, h: 0.42, fontSize: 20, fontFace: F.semi, valign: "middle" });
    // dashed core box
    const bx = 0.5, by = 2.35, bw = 5.95, bh = 3.0;
    s.addShape(pres.shapes.RECTANGLE, { x: bx, y: by, w: bw, h: bh, fill: { type: "none" }, line: { color: K.hi, width: 1.5, dashType: "dash" } });
    rect(s, bx + 0.6, by - 0.24, bw - 1.2, 0.48, "1A1A1A", { t: 15 });
    T(s, `CORE ISSUE OF ${who}`, { x: bx + 0.6, y: by - 0.24, w: bw - 1.2, h: 0.48, fontSize: 15, fontFace: F.semi, color: K.white, align: "center", valign: "middle" });
    T(s, coreBody, { x: bx + 0.3, y: by + 0.4, w: bw - 0.6, h: bh - 0.6, fontSize: 14, fontFace: F.med, color: K.white, align: "center", valign: "middle", lineSpacingMultiple: 1.1 });
    // symptoms with bracket
    const sx = 8.05, d = 0.7, top = 1.55, step = 1.08;
    T(s, "SYMPTOMS", { x: sx - 0.15, y: 1.0, w: 2, h: 0.35, fontSize: 14, fontFace: F.semi });
    const cy = (i) => top + i * step + d / 2;
    s.addShape(pres.shapes.LINE, { x: 7.55, y: cy(0), w: 0, h: cy(4) - cy(0), line: { color: K.ink, width: 1.25 } });
    s.addShape(pres.shapes.LINE, { x: bx + bw, y: by + bh / 2, w: 7.55 - (bx + bw), h: 0, line: { color: K.white, width: 1.25 } });
    for (let i = 0; i < 5; i++) {
      s.addShape(pres.shapes.LINE, { x: 7.55, y: cy(i), w: sx - 7.55, h: 0, line: { color: K.ink, width: 1.25 } });
      await limeIcon(s, sx, top + i * step, d, symptoms[i][0]);
      T(s, symptoms[i][1], { x: sx + 0.95, y: top + i * step - 0.05, w: W - sx - 0.95 - 0.35, h: d + 0.1, fontSize: 12, fontFace: F.reg, valign: "middle" });
    }
    strip(s);
  };
  await problem("LOCAL PHARMACIES", "interior.jpg",
    "PHARMACIES RUN A CREDIT BUSINESS WITH 10–50 SUPPLIERS ON PAPER, SO CASH CRUNCHES AND EXPIRY LOSSES STAY INVISIBLE UNTIL TOO LATE",
    [
      ["bc/warnsearch.png", "NO VIEW OF PROFIT, DUES OR STOCK: ONLY PAPER RECORDS"],
      ["bc/alarm.png", "CASH RUNS SHORT BEFORE BIG SUPPLIER PAYMENTS"],
      ["bc/gears.png", "EXPIRED STOCK IS PURE LOSS; RETURNS GO UNCLAIMED"],
      ["bc/cash.png", "PATIENTS BUY ON CREDIT WHILE THE SHOP OWES SUPPLIERS"],
      ["bc/coins.png", "NO WAY TO TELL THE CHEAPEST LOAN, OR IF ONE IS NEEDED"],
    ]);
  await problem("LENDERS", "bank.jpg",
    "LENDERS WANT SMALL-BUSINESS BORROWERS, BUT A PAPER-BASED PHARMACY GIVES THEM NOTHING TO VERIFY OR UNDERWRITE",
    [
      ["bc/cash.png", "NO AUDITED ACCOUNTS, TAX RETURNS OR DIGITAL RECORDS TO ASSESS"],
      ["bc/scam.png", "CAN'T TELL IF A PAPER INVOICE IS REAL OR ALREADY FINANCED"],
      ["bc/gears.png", "NO PRODUCT FOR A BDT 8,000–60,000 SUPPLIER GAP"],
      ["bc/coins.png", "MUST LEND 27% TO CMSMES BY 2029, BUT THE SHARE FELL TO 15.9% IN MARCH 2026"],
      ["bc/noentry.png", "FINANCIAL DATA NEEDS EXPLICIT CONSENT UNDER THE PDPO 2025"],
    ]);

  // 7. Three-way deadlock
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Problem" });
    T(s, "A 3 WAY DEADLOCK", { x: 0, y: 0.45, w: W, h: 0.6, fontSize: 30, fontFace: F.semi, align: "center" });
    const node = async (img, x, y, label, a, b) => {
      await fit(s, img, x - 0.75, y, 1.5, 1.3);
      T(s, label, { x: x - 2.0, y: y + 1.38, w: 4.0, h: 0.32, fontSize: 13, fontFace: F.semi, color: K.mid, align: "center" });
      T(s, [{ text: a, options: { breakLine: true } }, { text: b }], { x: x - 2.0, y: y + 1.7, w: 4.0, h: 0.62, fontSize: 12, fontFace: F.med, align: "center" });
    };
    s.addImage({ data: await icon(L.LuFactory, K.grey), x: W / 2 - 0.6, y: 1.25, w: 1.2, h: 1.2 });
    T(s, "MANUFACTURERS", { x: W / 2 - 2, y: 2.55, w: 4, h: 0.32, fontSize: 13, fontFace: F.semi, color: K.mid, align: "center" });
    T(s, [{ text: "MUST SELL ON CREDIT", options: { breakLine: true } }, { text: "CASH TRAPPED IN RECEIVABLES" }], { x: W / 2 - 2.0, y: 2.87, w: 4.0, h: 0.62, fontSize: 12, fontFace: F.med, align: "center" });
    await node("bc/shop.png", 2.75, 3.5, "PHARMACIES", "NEED MEDICINE EVERY DAY", "CAN'T PAY UPFRONT OR SEE CASH AHEAD");
    await node("bc/bank3d.png", W - 2.75, 3.5, "LENDERS", "WANT TO FINANCE", "BUT CAN'T VERIFY RISK");
    await fit(s, "bc/warn.png", W / 2 - 0.65, 3.9, 1.3, 1.15);
    s.addShape(pres.shapes.CURVED_DOWN_ARROW, { x: 3.2, y: 1.25, w: 2.6, h: 1.0, fill: { color: K.red }, line: { color: K.red, width: 0 }, flipH: true });
    s.addShape(pres.shapes.CURVED_DOWN_ARROW, { x: W - 5.8, y: 1.25, w: 2.6, h: 1.0, fill: { color: K.red }, line: { color: K.red, width: 0 } });
    s.addShape(pres.shapes.CURVED_UP_ARROW, { x: W / 2 - 1.6, y: 5.25, w: 3.2, h: 0.9, fill: { color: K.red }, line: { color: K.red, width: 0 } });
    banner(s, 1.6, 6.35, W - 3.2, 0.62, "Each side waits for another to move first: the pharmacy can't prove itself, the lender can't see it, and the manufacturer carries the gap.", K.deep, { size: 12 });
  }

  // 8. Core issue statement
  {
    const s = pres.addSlide({ masterName: "RED", sectionTitle: "Problem" });
    await fit(s, "bc/crack.png", 9.3, -0.4, 4.6, 3.3, "right", "top");
    s.addImage({ path: A("bc/crack.png"), x: 3.4, y: 5.1, w: 3.6, h: 2.6, rotate: 160 });
    T(s, "CORE ISSUE STATEMENT", { x: 0, y: 0.75, w: W, h: 0.55, fontSize: 24, fontFace: F.med, color: K.white, align: "center" });
    rrect(s, 1.25, 2.0, W - 2.5, 3.4, K.redSoft, { r: 0.05 });
    T(s, "A pharmacy already produces the evidence of a working business: invoices, payments and expiry dates. But it is trapped on paper, so no one can act on it in time, not the owner and not a lender.", {
      x: 1.6, y: 2.0, w: W - 3.2, h: 3.4, fontSize: 28, fontFace: F.med, color: K.white, align: "center", valign: "middle", lineSpacingMultiple: 1.1,
    });
  }

  // 9. Solution reveal
  pres.addSection({ title: "Solution" });
  {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Solution" });
    cover(s, "pharmacy.jpg", 0, 0, W, H);
    rect(s, 0, 0, W, H, "000000", { t: 35 });
    T(s, "What's the actual solution?", { x: 0, y: 0.75, w: W, h: 0.7, fontSize: 34, fontFace: F.xbold, color: K.white, align: "center" });
    T(s, "LaMP-Copilot", { x: 0, y: 1.55, w: W, h: 1.2, fontSize: 66, fontFace: F.xbold, color: K.bright, align: "center" });
    rect(s, 1.45, 3.05, 0.09, 1.65, K.bright);
    T(s, "An AI finance officer on the owner's phone: real accounts from paper, cash trouble spotted 30 days ahead, and every gap closed the cheapest way.", {
      x: 1.75, y: 3.0, w: W - 3.5, h: 1.75, fontSize: 20, fontFace: F.med, color: K.white, align: "center", valign: "middle",
    });
    rrect(s, 1.45, 5.55, 1.75, 0.38, K.bright, { r: 0.1 });
    s.addImage({ data: await icon(L.LuLightbulb, K.white), x: 1.53, y: 5.6, w: 0.28, h: 0.28 });
    T(s, "Justification", { x: 1.85, y: 5.55, w: 1.3, h: 0.38, fontSize: 12.5, fontFace: F.semi, color: K.white, valign: "middle" });
    T(s, [
      { text: "“The cheapest money is the cash you already have.” ", options: { fontFace: F.semi } },
      { text: "Trapped cash first, then free supplier time, and borrow only what's left." },
    ], { x: 1.45, y: 6.05, w: W - 2.9, h: 0.65, fontSize: 13, color: K.white });
  }

  // 10. One answer for each pain
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Solution" });
    ruleHead(s, "OUR SOLUTION: ONE ANSWER FOR EACH PAIN");
    const cols = [[1.35, 3.05, "THE PAIN", K.red2], [4.75, 4.3, "WHAT LaMP DOES", K.mid], [9.4, W - M - 9.4, "RESULT AT GREEN LIFE", K.deep]];
    cols.forEach(([x, w, t, c]) => { rect(s, x, 1.0, w, 0.36, c); T(s, t, { x, y: 1.0, w, h: 0.36, fontSize: 10.5, fontFace: F.semi, color: K.white, align: "center", valign: "middle", charSpacing: 1 }); });
    const rows = [
      ["bc/warnsearch.png", "No financial picture", "Paper records; real profit unknown.",
        "Reads invoice and sales-book photos into real accounts", "The owner confirms every figure.",
        "BDT 13,500", "monthly profit, finally visible"],
      ["bc/gears.png", "Expiry losses", "Returns go unclaimed.",
        "Tracks every batch's expiry and return window", "Drafts return claims with the invoice as evidence.",
        "BDT 9,200", "recovered: 68% of monthly profit"],
      ["bc/alarm.png", "Cash crunch before big orders", "The order is due before the cash.",
        "Forecasts 30 days across all 23 suppliers", "Trims slow movers; asks for more days.",
        "19,000 → 8,200", "shortfall, spotted 10 days early"],
      ["bc/coins.png", "No fair finance", "Lenders can't verify paper.",
        "Prices every option in taka; builds a credit passport", "Shared only with chosen lenders.",
        "BDT 0–182", "instead of BDT 422"],
    ];
    for (let i = 0; i < rows.length; i++) {
      const [ic, p, ps, a, as, b, bs] = rows[i];
      const y = 1.5 + i * 1.2, h = 1.08;
      await limeIcon(s, M, y + 0.17, 0.72, ic);
      rect(s, 1.35, y, 3.05, h, K.redTint); rect(s, 1.35, y, 0.06, h, K.red2);
      T(s, [{ text: p, options: { fontFace: F.semi, fontSize: 13, color: K.red, breakLine: true } }, { text: ps, options: { fontSize: 11.5 } }], { x: 1.55, y: y + 0.06, w: 2.75, h: h - 0.12, valign: "middle" });
      s.addShape(pres.shapes.RIGHT_ARROW, { x: 4.45, y: y + h / 2 - 0.15, w: 0.24, h: 0.3, fill: { color: K.grey }, line: { color: K.grey, width: 0 } });
      rect(s, 4.75, y, 4.3, h, K.mint); rect(s, 4.75, y, 0.06, h, K.bright);
      T(s, [{ text: a, options: { fontFace: F.semi, fontSize: 13, color: K.deep, breakLine: true } }, { text: as, options: { fontSize: 11.5 } }], { x: 4.95, y: y + 0.06, w: 4.0, h: h - 0.12, valign: "middle" });
      s.addShape(pres.shapes.RIGHT_ARROW, { x: 9.1, y: y + h / 2 - 0.15, w: 0.24, h: 0.3, fill: { color: K.grey }, line: { color: K.grey, width: 0 } });
      rect(s, 9.4, y, W - M - 9.4, h, K.deep);
      T(s, [{ text: b, options: { fontFace: F.semi, fontSize: 20, color: K.yellow, breakLine: true } }, { text: bs, options: { fontSize: 11.5, color: K.white } }], { x: 9.6, y: y + 0.06, w: W - M - 9.8, h: h - 0.12, valign: "middle" });
    }
    banner(s, M, 6.42, W - 2 * M, 0.55, "Every taka comes from deterministic code. The AI never computes or moves money.", K.deep, { size: 11.5 });
    strip(s);
  }

  // 11–15. How LaMP works (5 sequential steps)
  pres.addSection({ title: "How it works" });
  const step = async (n, title, actor, quote, rows, outcome, person, pbox) => {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "How it works" });
    const px = 10.3;
    rect(s, px, 0, W - px, H, K.bright);
    T(s, "How LaMP Works (5 Sequential Steps)", { x: 1.5, y: 0.42, w: 8.5, h: 0.6, fontSize: 26, fontFace: F.med, color: K.title, align: "right" });
    T(s, [{ text: `${n}. `, options: { color: K.bright } }, { text: title }], { x: M, y: 1.2, w: 9.4, h: 0.4, fontSize: 18, fontFace: F.med });
    T(s, actor, { x: M, y: 1.58, w: 9.4, h: 0.36, fontSize: 15, fontFace: F.reg, color: K.grey });
    rect(s, M, 2.1, 0.05, 0.92, K.ink);
    T(s, quote, { x: M + 0.18, y: 2.05, w: 8.75, h: 1.0, fontSize: 13.5, fontFace: F.reg, valign: "middle" });
    rows.forEach((t, i) => barRow(s, M, 3.25 + i * 0.68, 8.95, 0.58, t, { size: 12.5 }));
    rect(s, M, 5.42, 0.06, 0.38, K.bright);
    T(s, "Outcome", { x: M + 0.2, y: 5.42, w: 3, h: 0.38, fontSize: 16, fontFace: F.reg, valign: "middle" });
    await fit(s, "bc/check.png", M, 6.0, 0.42, 0.42);
    T(s, outcome, { x: M + 0.6, y: 5.88, w: 8.3, h: 0.72, fontSize: 15.5, fontFace: F.reg, valign: "middle" });
    await fit(s, person, pbox.x, pbox.y, pbox.w, H - pbox.y, "center", "bottom");
  };
  await step(1, "Capture (Turn Paper into Data)", "Owner's Phone · Pharmacy Counter",
    "The owner photographs invoices and sales-book pages; an OpenAI vision model reads batches, expiry dates, quantities, prices and due dates.",
    [
      "Unsure fields are highlighted; the owner fixes them before anything is saved.",
      "Plain-code checks verify totals and dates.",
      "Text in a photo is data: a planted “approve the maximum loan” is flagged.",
    ],
    "Paper becomes a verified record the owner has confirmed.", "step-phone.png", { x: 9.6, y: 3.6, w: 3.6 });
  await step(2, "Understand (Build Real Accounts)", "LaMP Engines · Deterministic Python",
    "From confirmed records, LaMP builds the accounts a lender would ask for: profit, margin, stock days and money in expiring stock.",
    [
      "Green Life: sales BDT 412,500, net profit BDT 13,500 at a 12% margin.",
      "6 batches worth BDT 18,400 expire within 60 days; BDT 9,200 is still returnable.",
      "LaMP drafts the return claims with the invoice attached.",
    ],
    "Profit, dues, stock and expiry on one screen.", "step-check.png", { x: 9.55, y: 3.6, w: 3.75 });
  await step(3, "Anticipate (Forecast and Alert)", "30-Day Cash Forecast · All 23 Suppliers",
    "A 30-day forecast combines sales, patient dues, supplier dues, rent, salaries and orders, and marks the first day cash runs out.",
    [
      "Supplier A's BDT 60,000 order is due Mon 26 Oct; cash that day: BDT 41,000.",
      "Alert ten days ahead: short BDT 19,000.",
      "Also flags expiring stock, closing return windows and overdue patient dues.",
    ],
    "Cash trouble shows up while it's still cheap to fix.", "step-order.png", { x: 9.5, y: 3.3, w: 3.8 });
  await step(4, "Fund (Cheapest Money First)", "Funding Plan · Owner Approval",
    "30 boxes of a slow mover sell 0.2 a day with 60 sellable days left, so only 12 will sell before expiry.",
    [
      "Trim to 12 boxes: BDT 10,800 saved, gap down from BDT 19,000 to BDT 8,200.",
      "Options in taka: supplier extension free, wallet loan BDT 182, bank supplier credit BDT 492.",
      "Plan: ask for 20 more days, with the wallet loan as the day-7 fallback. The owner approves each step.",
    ],
    "BDT 0–182 instead of BDT 422, and no stock left to expire.", "step-cash.png", { x: 9.75, y: 3.1, w: 3.4 });
  await step(5, "Prove (Credit Passport and Consent)", "Lender View · Sandbox Partners",
    "38 of 41 supplier-confirmed invoices paid on time become a credit passport: on-time estimate 0.826, default risk 3%.",
    [
      "A lender's rule turns that into a 75.2% advance; the lender decides in its own view.",
      "Shared only with lenders the owner switches on; withdrawable any time (PDPO 2025).",
      "A registry locks each invoice so it can't be financed twice.",
    ],
    "A verifiable, consented path to fair finance.", "step-shield.png", { x: 9.7, y: 3.7, w: 3.6 });

  // 16. Product, live
  pres.addSection({ title: "Product" });
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Product" });
    ruleHead(s, "THE COPILOT, LIVE ON GREEN LIFE'S DATA");
    const phones = [["today-m.png", "Today"], ["funding-m.png", "Funding"], ["passport-m.png", "Credit passport"]];
    for (let i = 0; i < 3; i++) {
      const x = M + 0.1 + i * 2.75, y = 1.05, sw = 2.35, sh = (sw * 1688) / 780;
      const fh = Math.min(sh + 0.16, 5.6);
      rrect(s, x, y, sw + 0.16, fh, "1C1C1C", { r: 0.12 });
      s.addImage({ path: A(phones[i][0]), x: x + 0.08, y: y + 0.08, w: sw, h: fh - 0.16, sizing: { type: "crop", x: 0, y: 0, w: sw, h: fh - 0.16 } });
      T(s, phones[i][1], { x, y: y + fh + 0.08, w: sw + 0.16, h: 0.3, fontSize: 11.5, fontFace: F.semi, color: K.mid, align: "center" });
    }
    const rx = 8.95, rw = W - M - rx;
    T(s, "What the owner sees", { x: rx, y: 1.05, w: rw, h: 0.35, fontSize: 14, fontFace: F.semi });
    const rows = [
      ["Today", "The banner names the next shortfall: Short BDT 19,000, Mon 26 Oct, in 10 days."],
      ["Funding", "BDT 8,200 left after the trim, a three-step plan, every option in taka. The owner approves."],
      ["Credit passport", "38 of 41 on time, a 75.2% advance offer, and a sharing switch per lender."],
    ];
    rows.forEach(([h, t], i) => barRow(s, rx, 1.5 + i * 1.22, rw, 1.1, [{ text: h + ": ", options: { fontFace: F.semi } }, { text: t }], { size: 12 }));
    rrect(s, rx, 5.25, rw, 1.45, K.deep, { r: 0.05 });
    T(s, [
      { text: "Built and running", options: { fontFace: F.semi, color: K.lime, breakLine: true } },
      { text: "Next.js · FastAPI · PostgreSQL · OpenAI Responses API · live audit log · 73 automated tests", options: { color: K.white } },
    ], { x: rx + 0.2, y: 5.25, w: rw - 0.4, h: 1.45, fontSize: 11.5, valign: "middle" });
    strip(s);
  }

  // 17. System flow
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Product" });
    head(s, "SYSTEM", "FLOW", { bColor: K.bright, size: 16 });
    T(s, [{ text: "AI READS AND PROPOSES, CODE CALCULATES — " }, { text: "AND ONLY THE OWNER CAN APPROVE MONEY MOVING", options: { color: K.red } }], { x: M, y: 0.92, w: 12.3, h: 0.4, fontSize: 14.5, fontFace: F.semi });
    const bw = 1.88, gap = 0.17, x0 = M, by = 2.75, bh = 1.05;
    const steps = [
      [L.LuCamera, "Photo Capture"], [L.LuScanText, "AI Extraction"], [L.LuUserCheck, "Owner Confirms"],
      [L.LuCalculator, "Engines Calculate"], [L.LuBadgeCheck, "Owner Approves"], [L.LuPlay, "Sandbox Executes"],
    ];
    for (let i = 0; i < 6; i++) {
      const x = x0 + i * (bw + gap);
      rrect(s, x, by, bw, bh, K.mint, { line: { color: K.bright, width: 1.25 }, r: 0.08 });
      rrect(s, x + 0.08, by + 0.08, 0.36, 0.22, K.bright, { r: 0.2 });
      T(s, `0${i + 1}`, { x: x + 0.08, y: by + 0.08, w: 0.36, h: 0.22, fontSize: 8, fontFace: F.semi, color: K.white, align: "center", valign: "middle" });
      s.addImage({ data: await icon(steps[i][0], K.mid), x: x + bw / 2 - 0.2, y: by + 0.22, w: 0.4, h: 0.4 });
      T(s, steps[i][1], { x, y: by + 0.66, w: bw, h: 0.32, fontSize: 10.5, fontFace: F.semi, align: "center" });
      if (i < 5) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + bw + 0.01, y: by + bh / 2 - 0.08, w: gap - 0.02, h: 0.16, fill: { color: K.ink }, line: { color: K.ink, width: 0 } });
    }
    const svc = [[1, "OpenAI Responses API (vision)"], [3, "Copilot chat: read-only tools"], [5, "Lender sandbox (consented)"]];
    T(s, "OUTSIDE SERVICES", { x: x0, y: 1.6, w: 1.6, h: 0.3, fontSize: 8, fontFace: F.semi, color: K.mute, charSpacing: 1 });
    svc.forEach(([i, t]) => {
      const x = x0 + i * (bw + gap);
      rrect(s, x - 0.05, 1.9, bw + 0.1, 0.4, "EFEFEF", { r: 0.1 });
      T(s, t, { x: x - 0.05, y: 1.9, w: bw + 0.1, h: 0.4, fontSize: 8.5, fontFace: F.semi, align: "center", valign: "middle" });
      s.addShape(pres.shapes.LINE, { x: x + bw / 2, y: 2.3, w: 0, h: by - 2.3, line: { color: K.mute, width: 1, dashType: "dash", endArrowType: "triangle" } });
    });
    const ey = 4.2;
    for (let i = 0; i < 6; i++) {
      const x = x0 + i * (bw + gap) + bw / 2;
      s.addShape(pres.shapes.LINE, { x, y: by + bh, w: 0, h: ey - by - bh, line: { color: K.bright, width: 1.25, endArrowType: "triangle" } });
    }
    rrect(s, x0, ey, W - 2 * M, 1.12, "4CB877", { r: 0.06 });
    T(s, [{ text: "DETERMINISTIC ENGINES", options: { fontFace: F.semi } }, { text: "   plain Python, the only place money is computed", options: { fontFace: F.reg } }], { x: x0 + 0.2, y: ey + 0.08, w: 9, h: 0.3, fontSize: 10, color: K.white });
    const pills = ["Accounts", "Dues", "Forecast", "Expiry", "Orders & trim", "Credit passport", "Funding plan", "Registry", "Actions"];
    const pw = (W - 2 * M - 0.4 - 8 * 0.1) / 9;
    pills.forEach((p, i) => {
      const x = x0 + 0.2 + i * (pw + 0.1);
      rrect(s, x, ey + 0.5, pw, 0.42, K.white, { r: 0.08 });
      T(s, p, { x, y: ey + 0.5, w: pw, h: 0.42, fontSize: 9, fontFace: F.semi, align: "center", valign: "middle" });
    });
    const dy = 5.75;
    const dash = (x, w, runs) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: dy, w, h: 0.5, rectRadius: 0.08, fill: { type: "none" }, line: { color: K.mute, width: 1, dashType: "dash" } });
      T(s, runs, { x, y: dy, w, h: 0.5, fontSize: 10, fontFace: F.semi, align: "center", valign: "middle" });
    };
    dash(x0, 3.95, [{ text: "AI agent — " }, { text: "cannot approve, pay or contact anyone", options: { color: K.red } }]);
    dash(x0 + 4.15, 3.95, [{ text: "PostgreSQL — " }, { text: "seed, captures, actions", options: { color: K.mid } }]);
    dash(x0 + 8.3, W - 2 * M - 8.3, [{ text: "Audit log — " }, { text: "every event, T0–T3, streamed live", options: { color: K.mid } }]);
    strip(s);
  }

  // 18. Trust mechanism
  pres.addSection({ title: "Trust" });
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Trust" });
    head(s, "TRUST MECHANISM", "", { size: 24 });
    T(s, "How LaMP makes AI misuse and double financing structurally impossible, not just against the rules", { x: M, y: 0.95, w: 11, h: 0.32, fontSize: 12, fontFace: F.reg, italic: true, color: K.grey });
    const cw = (W - 2 * M - 0.35) / 2;
    const cols = [
      ["Can anyone trick the AI into moving money?", "No — there is no tool to do it", [
        [L.LuLock, "Read-only tools plus one proposal", "The chat can read and propose. No tool approves, pays or contacts anyone."],
        [L.LuBan, "Approval lives outside the AI", "Only the owner approves, in the app; code then runs the step in a sandbox."],
        [L.LuScanText, "Text in photos is data", "A planted “approve the maximum loan” is flagged, and nothing happens."],
      ]],
      ["Can one invoice be financed twice, or data leak to a lender?", "No — registry lock and consent", [
        [L.LuFingerprint, "One invoice, one financing", "Each invoice's fingerprint is locked; a second application is rejected."],
        [L.LuUserCheck, "Consent per lender and scope", "Lenders see only what the owner shares, withdrawable any time."],
        [L.LuEyeOff, "No patient medicine data", "Patient dues are amounts only; purchases are health data."],
      ]],
    ];
    for (let c = 0; c < 2; c++) {
      const x = M + c * (cw + 0.35);
      const [q, a, items] = cols[c];
      rrect(s, x, 1.45, cw, 0.5, "C9403A", { r: 0.06 });
      T(s, q, { x: x + 0.2, y: 1.45, w: cw - 0.4, h: 0.5, fontSize: 13, fontFace: F.semi, color: K.white, valign: "middle" });
      T(s, a, { x, y: 2.05, w: cw, h: 0.3, fontSize: 11.5, fontFace: F.semi, color: K.mid });
      for (let i = 0; i < 3; i++) {
        const y = 2.45 + i * 1.12;
        rrect(s, x, y, cw, 1.0, K.mint, { r: 0.05 });
        await circleIcon(s, x + 0.2, y + 0.2, 0.6, items[i][0], K.mid);
        T(s, items[i][1], { x: x + 1.0, y: y + 0.1, w: cw - 1.15, h: 0.3, fontSize: 12, fontFace: F.semi });
        T(s, items[i][2], { x: x + 1.0, y: y + 0.4, w: cw - 1.15, h: 0.55, fontSize: 11.5, color: K.grey });
      }
    }
    banner(s, M, 5.95, W - 2 * M, 0.75, "The guarantee is structural: the tools the AI would need don't exist, and every decision is logged.", "1F7A47", { size: 12, align: "left" });
    strip(s);
  }

  // 19. Security & compliance
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Trust" });
    ruleHead(s, "SECURITY & COMPLIANCE");
    const lw = 6.0;
    T(s, "Permission Tiers", { x: M, y: 1.0, w: lw, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    s.addTable([
      tableHead(["Tier", "Who", "What it may do"]),
      [cell("T0", { font: F.semi }), cell("Regulator, auditor"), cell("Read-only audit views")],
      [cell("T1", { font: F.semi }), cell("Owner, photo reading"), cell("Capture, confirm, approve own actions")],
      [cell("T2", { font: F.semi }), cell("Engines"), cell("Compute; no outside contact")],
      [cell("T3", { font: F.semi }), cell("Lenders, money steps"), cell("Consented reads, sandbox payouts")],
    ], { x: M, y: 1.33, w: lw, colW: [0.55, 1.75, 3.7], rowH: 0.42, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    const rx = M + lw + 0.3, rw = W - M - rx;
    T(s, "What's Real and What's Sandbox in This Prototype", { x: rx, y: 1.0, w: rw, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    s.addTable([
      tableHead(["Real, working code", "Sandbox, said openly"]),
      [cell("Photo reading (OpenAI vision)"), cell("Lenders, decisions, payouts")],
      [cell("All money maths"), cell("Supplier replies")],
      [cell("Copilot chat, read-only tools"), cell("Supplier invoice confirmation (seeded)")],
      [cell("Approvals, consent, duplicate guard, audit log"), cell("Federated learning (roadmap)")],
    ], { x: rx, y: 1.33, w: rw, colW: [rw / 2, rw / 2], rowH: 0.42, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    const tiles = [["73 / 73", "tests pass, no AI calls"], ["0", "money figures computed by the AI"], ["Every", "state change logged and streamed"], ["Per lender", "consent, withdrawable"]];
    const tw = (W - 2 * M - 0.6) / 4;
    tiles.forEach(([b, t], i) => {
      const x = M + i * (tw + 0.2);
      rrect(s, x, 3.75, tw, 1.35, K.white, { line: { color: K.bright, width: 1.25 }, r: 0.06 });
      T(s, b, { x, y: 3.85, w: tw, h: 0.55, fontSize: 24, fontFace: F.semi, color: K.mid, align: "center" });
      T(s, t, { x: x + 0.15, y: 4.42, w: tw - 0.3, h: 0.6, fontSize: 10, align: "center" });
    });
    barRow(s, M, 5.35, 6.0, 1.0, "Execution evidence: every event is exported with its tier to logs/sandbox_execution_trace.log.", { size: 12 });
    rrect(s, M + 6.3, 5.35, W - 2 * M - 6.3, 1.0, K.redTint, { line: { color: K.red2, width: 1 }, r: 0.05 });
    T(s, "Lenders, payouts and supplier replies are sandbox partners. No real money moves.", { x: M + 6.5, y: 5.35, w: W - 2 * M - 6.7, h: 1.0, fontSize: 12.5, fontFace: F.semi, color: K.red, valign: "middle" });
    strip(s);
  }

  // 20. What makes it new
  pres.addSection({ title: "Market" });
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Market" });
    ruleHead(s, "INNOVATION: WHAT MAKES LaMP NEW");
    rrect(s, M, 0.95, W - 2 * M, 0.5, null, { line: { color: K.bright, width: 1 }, r: 0.06 });
    T(s, [
      { text: "Four things no pharmacy tool in Bangladesh does today, each working in the prototype.", options: { fontFace: F.semi } },
    ], { x: M + 0.2, y: 0.95, w: W - 2 * M - 0.4, h: 0.5, fontSize: 11, valign: "middle" });
    const cards = [
      ["bc/alarm.png", "WORKING CAPITAL · EXPIRY-AWARE", "Orders and credit sized on what will actually sell", "BDT 10,800", "of stock avoided on one order",
        "Sales rate and days to expiry decide how much will sell; orders and credit are sized on that."],
      ["bc/shop.png", "NEUTRAL · MULTI-SUPPLIER", "Works across every supplier, not one distributor", "10–50", "suppliers per pharmacy",
        "Dues, returns and financing across all suppliers, not one distributor's orders."],
      ["bc/credit.png", "CREDIT · CONSENTED PASSPORT", "Supplier payments become lender evidence", "75.2%", "advance on 38 of 41 on time",
        "A supplier-confirmed record replaces missing collateral, shared per lender with consent."],
      [L.LuShieldCheck, "AGENTIC · SAFE BY DESIGN", "An agent that acts, without touching money", "0", "money figures computed by the AI",
        "It reads, forecasts and prepares actions; code computes every taka, and the owner approves."],
    ];
    const cw = (W - 2 * M - 0.3) / 2, ch = 2.05;
    for (let i = 0; i < 4; i++) {
      const [ic, k, t, big, bigs, b] = cards[i];
      const x = M + (i % 2) * (cw + 0.3), y = 1.68 + Math.floor(i / 2) * (ch + 0.2);
      rect(s, x, y, cw, ch, K.mint);
      rect(s, x, y, 0.06, ch, K.bright);
      if (typeof ic === "string") await limeIcon(s, x + 0.28, y + 0.25, 0.7, ic);
      else {
        rrect(s, x + 0.28, y + 0.25, 0.7, 0.7, "5FE35F", { r: 0.18 });
        s.addImage({ data: await icon(ic, K.ink), x: x + 0.43, y: y + 0.4, w: 0.4, h: 0.4 });
      }
      T(s, k, { x: x + 1.15, y: y + 0.24, w: cw - 3.35, h: 0.25, fontSize: 8.5, fontFace: F.semi, color: K.mid, charSpacing: 1 });
      T(s, t, { x: x + 1.15, y: y + 0.48, w: cw - 3.35, h: 0.55, fontSize: 12.5, fontFace: F.semi });
      rrect(s, x + cw - 2.0, y + 0.22, 1.8, 0.95, K.deep, { r: 0.06 });
      T(s, [{ text: big, options: { fontSize: 20, fontFace: F.semi, color: K.yellow, breakLine: true } }, { text: bigs, options: { fontSize: 8.5, color: K.white } }], { x: x + cw - 1.95, y: y + 0.22, w: 1.7, h: 0.95, align: "center", valign: "middle" });
      T(s, b, { x: x + 0.28, y: y + 1.25, w: cw - 0.5, h: 0.72, fontSize: 12, color: K.grey, valign: "middle" });
    }
    banner(s, M, 6.15, W - 2 * M, 0.7, "No one else combines all four: pharmacy-specific, neutral across suppliers, consented, and safe by design.", K.deep, { size: 12.5 });
    strip(s);
  }

  // 21. Competitive landscape
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Market" });
    ruleHead(s, "COMPETITIVE LANDSCAPE");
    rrect(s, M, 0.95, W - 2 * M, 0.55, null, { line: { color: K.bright, width: 1 }, r: 0.06 });
    T(s, [{ text: "Others prove the demand; ", options: { fontFace: F.semi } }, { text: "none is neutral, pharmacy-aware, agentic and capital-light at once." }], { x: M + 0.2, y: 0.95, w: W - 2 * M - 0.4, h: 0.55, fontSize: 11, valign: "middle" });
    const yes = (t = "Yes") => cell(t, { color: K.mid, font: F.semi, align: "center" });
    const no = (t = "No") => cell(t, { color: K.red, font: F.semi, align: "center" });
    const part = (t = "Partly") => cell(t, { color: "B7791F", font: F.semi, align: "center" });
    const us = (t) => cell(t, { fill: K.mint, font: F.semi, color: K.deep, align: "center" });
    s.addTable([
      tableHead(["Player", "Model", "Neutral across suppliers", "Knows batches and expiry", "Acts, not just records", "No stock or capital on its books"]),
      [cell("PulseTech (Bangladesh)", { font: F.semi }), cell("Distributor finance; 12,000+ Dhaka pharmacies"), no("No: own orders"), yes(), part(), no()],
      [cell("TallyKhata (Bangladesh)", { font: F.semi }), cell("Bookkeeping for any merchant; 4.4M users"), yes(), no("No: any shop"), no(), yes()],
      [cell("Shelf Life (Nigeria, Kenya)", { font: F.semi }), cell("Pay-as-you-sell pharmacy stock"), no(), yes(), part(), no("No: holds stock")],
      [cell("Retailio (India)", { font: F.semi }), cell("Marketplace credit; 100,000+ pharmacies"), no("No: own marketplace"), part(), part(), yes()],
      [cell("LaMP-Copilot", { font: F.semi, fill: K.mint, color: K.deep }), cell("AI finance officer across all suppliers", { fill: K.mint }), us("Yes"), us("Yes"), us("Yes"), us("Yes")],
    ], { x: M, y: 1.7, w: W - 2 * M, colW: [2.2, 3.85, 1.55, 1.55, 1.5, 1.58], rowH: 0.6, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    const edges = [
      ["vs PulseTech", "Neutral across all 10–50 suppliers."],
      ["vs TallyKhata", "Pharmacy-specific and agentic."],
      ["vs Shelf Life", "No stock or capital on our books."],
    ];
    const ew = (W - 2 * M - 0.4) / 3;
    edges.forEach(([h, t], i) => barRow(s, M + i * (ew + 0.2), 5.6, ew, 0.85, [{ text: h, options: { fontFace: F.semi, color: K.deep, breakLine: true } }, { text: t }], { size: 12 }));
    T(s, "Sources: Financial Express, Startup Bangladesh, The Daily Star, Accion, TechCabal, BioSpectrum, FinBox.", { x: M, y: 6.6, w: W - 2 * M, h: 0.3, fontSize: 7.5, color: K.mute });
    strip(s);
  }

  // 22. Revenue model
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Market" });
    ruleHead(s, "REVENUE MODEL");
    rrect(s, M, 0.95, W - 2 * M, 0.75, null, { line: { color: K.bright, width: 1 }, r: 0.06 });
    T(s, [
      { text: "Primary: ", options: { fontFace: F.semi } },
      { text: "an origination fee from partner lenders.   " },
      { text: "Second: ", options: { fontFace: F.semi } },
      { text: "manufacturer and distributor programmes." },
    ], { x: M + 0.2, y: 0.95, w: W - 2 * M - 0.4, h: 0.75, fontSize: 13, valign: "middle" });
    T(s, "Who Pays LaMP", { x: M, y: 1.9, w: 6, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    const who = [
      [L.LuStore, "Pharmacy", "Pays nothing; free is our adoption lever."],
      [L.LuLandmark, "Partner lender", "Gets verified, consented borrowers."],
      [L.LuFactory, "Manufacturer or distributor", "Gets faster collections and evidence-backed returns."],
    ];
    const ww = 1.95;
    for (let i = 0; i < 3; i++) {
      const x = M + i * (ww + 0.12);
      rrect(s, x, 2.25, ww, 2.05, K.white, { line: { color: "E3E3E3", width: 0.75 }, r: 0.05 });
      rrect(s, x + ww / 2 - 0.25, 2.4, 0.5, 0.5, K.mid, { r: 0.12 });
      s.addImage({ data: await icon(who[i][0], K.white), x: x + ww / 2 - 0.15, y: 2.5, w: 0.3, h: 0.3 });
      T(s, who[i][1], { x: x + 0.1, y: 2.98, w: ww - 0.2, h: 0.45, fontSize: 10.5, fontFace: F.semi, align: "center", valign: "middle" });
      T(s, who[i][2], { x: x + 0.12, y: 3.48, w: ww - 0.24, h: 0.8, fontSize: 10.5, color: K.grey, align: "center" });
    }
    const rx = 6.95, rw = W - M - rx;
    T(s, "Revenue Streams (proposed, to be validated in the pilot)", { x: rx, y: 1.9, w: rw, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    s.addTable([
      tableHead(["Stream", "Payer", "Charged on", "Proposed rate"]),
      [cell("Origination fee", { font: F.semi }), cell("Partner lender"), cell("Amount advanced"), cell("1.0%", { font: F.semi, color: K.mid })],
      [cell("Programme subscription", { font: F.semi }), cell("Manufacturer or distributor"), cell("Per company, per month"), cell("BDT 2.5–3.5 lakh", { font: F.semi, color: K.mid })],
      [cell("Pharmacy app", { font: F.semi }), cell("Pharmacy"), cell("—"), cell("Free", { font: F.semi, color: K.mid })],
    ], { x: rx, y: 2.25, w: rw, colW: [1.6, 1.55, 1.45, 1.23], rowH: 0.5, border: { type: "solid", pt: 0.5, color: K.line }, margin: [0, 0.08, 0, 0.08] });
    T(s, "Pricing Logic", { x: M, y: 4.55, w: 6, h: 0.3, fontSize: 12.5, fontFace: F.semi });
    barRow(s, M, 4.9, 6.1, 0.85, "Lenders already pay to acquire borrowers; a verified applicant is cheaper to approve.", { size: 12 });
    barRow(s, M, 5.85, 6.1, 0.85, "Recovered expiry and on-time collections are worth more than the subscription.", { size: 12 });
    rrect(s, rx, 4.55, rw, 2.15, K.white, { line: { color: K.bright, width: 1.25 }, r: 0.06 });
    rect(s, rx, 4.55, rw, 0.42, K.mid);
    T(s, "Why this model is capital-light", { x: rx, y: 4.55, w: rw, h: 0.42, fontSize: 11.5, fontFace: F.semi, color: K.white, align: "center", valign: "middle" });
    T(s, "LaMP never lends or holds funds. Lenders supply capital and carry risk; we supply verification. No stock, no loan book.", { x: rx + 0.25, y: 5.05, w: rw - 0.5, h: 1.55, fontSize: 13.5, align: "center", valign: "middle" });
    strip(s);
  }

  // 23. Feasibility
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Market" });
    head(s, "FEASIBILITY", "", { color: K.bright, size: 22 });
    const hx = [1.15, 4.3, 7.45, 10.6], hw = [3.0, 3.0, 3.0, 2.18];
    const hd = [[L.LuTriangleAlert, "RISK EVENTS", "C00000"], [L.LuUndo2, "MITIGATION", "2E75B6"], [L.LuRotateCcw, "CONTINGENCY", K.mid], [L.LuCircleCheck, "RISK LEVEL", "7030A0"]];
    for (let i = 0; i < 4; i++) {
      s.addImage({ data: await icon(hd[i][0], hd[i][2]), x: hx[i], y: 1.12, w: 0.3, h: 0.3 });
      T(s, hd[i][1], { x: hx[i] + 0.38, y: 1.1, w: hw[i] - 0.4, h: 0.34, fontSize: 13, fontFace: F.med, color: hd[i][2], valign: "middle" });
    }
    const rows = [
      ["A", "Owners skip invoices", "Capture takes a minute and pays off at once", "Distributors upload e-invoices", "Medium", K.blue, K.blueTint],
      ["B", "AI misreads a figure", "Owner confirms every field; code checks totals", "Manual entry fallback", "Medium", K.bright, K.mint],
      ["C", "Lenders distrust the record", "Supplier-confirmed invoices, cautious score", "Shadow mode with one lender first", "High", K.red2, K.redTint],
      ["D", "Privacy breach or AI misuse", "Consent per lender, no patient data, no money tools", "Legal review and red-team tests", "High", K.red2, K.redTint],
    ];
    rows.forEach(([id, r, m, c, lvl, col, tint], i) => {
      const y = 1.6 + i * 1.3, h = 1.15;
      rect(s, M, y, 0.45, h, K.white, { line: { color: col, width: 1.25 } });
      T(s, id, { x: M, y, w: 0.45, h, fontSize: 15, fontFace: F.semi, color: col, align: "center", valign: "middle" });
      [r, m, c, lvl].forEach((t, j) => {
        rect(s, hx[j], y, hw[j], h, tint, { line: { color: col, width: 1.25 } });
        T(s, t, { x: hx[j] + 0.12, y, w: hw[j] - 0.24, h, fontSize: j === 3 ? 15 : 13, fontFace: j === 3 ? F.semi : F.reg, align: "center", valign: "middle" });
      });
    });
  }

  // 24. Action plan & roadmap
  pres.addSection({ title: "Close" });
  {
    const s = pres.addSlide({ masterName: "PLAIN", sectionTitle: "Close" });
    T(s, "Action Plan & Roadmap", { x: M, y: 0.35, w: 7, h: 0.6, fontSize: 28, fontFace: F.semi, color: K.deep });
    T(s, "From one pharmacy in Bogura to nationwide impact", { x: M, y: 0.92, w: 7, h: 0.35, fontSize: 14, color: K.mid });
    s.addShape(pres.shapes.LINE, { x: 7.55, y: 0.45, w: 0, h: 0.8, line: { color: K.line, width: 1 } });
    T(s, "Prove it with real invoices and repayments, grow across suppliers, then become the neutral finance layer.", { x: 7.75, y: 0.4, w: 5.05, h: 0.9, fontSize: 12, color: K.grey, valign: "middle" });
    const phases = [
      ["Pilot", "0–6 months", "Prove the model with 20 pharmacies in Bogura.", [L.LuStore, L.LuSmartphone, L.LuLandmark], ["Pharmacies", "Copilot", "Lender"],
        ["20 pharmacies, one distributor", "One lender, shadow mode first", "Measure accuracy and forecast error"],
        ["80%+ of invoices captured", "First loans repaid on time"]],
      ["Network", "6–18 months", "Grow across suppliers and districts.", [L.LuFactory, L.LuStore, L.LuBadgeCheck], ["Distributors", "More shops", "Passports"],
        ["Distributor programmes", "Bangla interface", "Passports with 3+ lenders"],
        ["500+ pharmacies", "3+ distributors"]],
      ["Scale", "18–36 months", "Become the neutral finance layer for pharmacies.", [L.LuLandmark, L.LuNetwork, L.LuMap], ["Banks", "Shared risk", "Nationwide"],
        ["Bank supplier-credit product", "Federated risk model across lenders", "Nationwide rollout"],
        ["5,000+ pharmacies", "BDT 100M+ financed"]],
    ];
    const cw = (W - 2 * M - 0.5) / 3;
    for (let i = 0; i < 3; i++) {
      const x = M + i * (cw + 0.25), y = 1.5, h = 4.5;
      const [n, t, d, ics, labels, acts, mets] = phases[i];
      rrect(s, x, y, cw, h, K.white, { line: { color: "BFE6CC", width: 1 }, r: 0.04 });
      s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: y + 0.15, w: 0.42, h: 0.42, fill: { color: K.mid }, line: { color: K.mid, width: 0 } });
      T(s, String(i + 1), { x: x + 0.15, y: y + 0.15, w: 0.42, h: 0.42, fontSize: 14, fontFace: F.semi, color: K.white, align: "center", valign: "middle" });
      T(s, [{ text: n + "  ", options: { fontFace: F.semi, color: K.deep } }, { text: `(${t})`, options: { color: K.grey, fontSize: 11 } }], { x: x + 0.68, y: y + 0.12, w: cw - 0.8, h: 0.3, fontSize: 14 });
      T(s, d, { x: x + 0.68, y: y + 0.42, w: cw - 0.8, h: 0.25, fontSize: 9.5, color: K.grey });
      for (let k = 0; k < 3; k++) {
        const ix = x + 0.35 + k * ((cw - 0.7) / 3);
        s.addImage({ data: await icon(ics[k], K.mid), x: ix + 0.32, y: y + 0.82, w: 0.42, h: 0.42 });
        T(s, labels[k], { x: ix, y: y + 1.27, w: 1.06, h: 0.22, fontSize: 8, align: "center" });
        if (k < 2) T(s, "→", { x: ix + 0.95, y: y + 0.86, w: 0.3, h: 0.3, fontSize: 14, color: K.mid, align: "center" });
      }
      rect(s, x + 0.12, y + 1.6, cw - 0.24, 1.6, K.mint);
      T(s, "Key Actions", { x: x + 0.25, y: y + 1.66, w: cw - 0.5, h: 0.25, fontSize: 10, fontFace: F.semi });
      T(s, acts.map((a, k) => ({ text: a, options: { bullet: { indent: 10 }, breakLine: k < acts.length - 1 } })), { x: x + 0.25, y: y + 1.95, w: cw - 0.45, h: 1.2, fontSize: 11.5, paraSpaceAfter: 5 });
      rect(s, x + 0.12, y + 3.3, cw - 0.24, 1.08, K.mint);
      T(s, "Success Metrics (targets)", { x: x + 0.25, y: y + 3.35, w: cw - 0.5, h: 0.25, fontSize: 10, fontFace: F.semi });
      T(s, mets.map((a, k) => ({ text: a, options: { bullet: { indent: 10 }, breakLine: k < mets.length - 1 } })), { x: x + 0.25, y: y + 3.62, w: cw - 0.45, h: 0.72, fontSize: 11.5 });
      if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + cw + 0.04, y: y + h / 2 - 0.1, w: 0.17, h: 0.2, fill: { color: K.mid }, line: { color: K.mid, width: 0 } });
    }
    rrect(s, M, 6.15, W - 2 * M, 0.95, "F4FBF6", { line: { color: "BFE6CC", width: 1 }, r: 0.04 });
    T(s, [{ text: "Long-Term Impact", options: { fontFace: F.semi, color: K.deep, fontSize: 13 } }], { x: M + 0.2, y: 6.2, w: 2.55, h: 0.85, valign: "middle" });
    const imp = [[L.LuBadgeCheck, "Bankable pharmacies", "Verified records replace missing collateral"], [L.LuTimer, "Less expired medicine", "Orders sized on what will sell"], [L.LuHandCoins, "Cheaper finance", "Own cash first, cheapest credit last"], [L.LuHeartPulse, "Healthier Bangladesh", "Fewer stock-outs, more medicine on shelves"]];
    const iw = (W - 2 * M - 3.0) / 4;
    for (let k = 0; k < 4; k++) {
      const x = M + 2.95 + k * iw;
      s.addImage({ data: await icon(imp[k][0], K.mid), x, y: 6.38, w: 0.42, h: 0.42 });
      T(s, [{ text: imp[k][1], options: { fontFace: F.semi, fontSize: 10, color: K.deep, breakLine: true } }, { text: imp[k][2], options: { fontSize: 8.5, color: K.grey } }], { x: x + 0.5, y: 6.2, w: iw - 0.55, h: 0.85, valign: "middle" });
    }
  }

  // 25. Closing
  {
    const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Close" });
    cover(s, "pharmacy.jpg", 0, 0, W, H);
    rect(s, 0, 0, W, H, "000000", { t: 38 });
    await fit(s, "bc/logo.png", W / 2 - 0.6, 0.55, 1.2, 1.2);
    T(s, [{ text: "Every pharmacy already has a " }, { text: "credit history", options: { color: K.bright } }, { text: "." }], { x: 0.8, y: 1.95, w: W - 1.6, h: 0.8, fontSize: 36, fontFace: F.xbold, color: K.white, align: "center" });
    T(s, "LaMP-Copilot puts it to work.", { x: 0.8, y: 2.75, w: W - 1.6, h: 0.6, fontSize: 26, fontFace: F.med, color: K.white, align: "center" });
    rrect(s, W / 2 - 4.6, 3.85, 9.2, 0.95, K.bright, { r: 0.12 });
    T(s, [{ text: "Our ask", options: { fontFace: F.semi, breakLine: true } }, { text: "Introductions to one partner lender and one distributor for a six-month pilot with 20 pharmacies in Bogura." }], { x: W / 2 - 4.4, y: 3.85, w: 8.8, h: 0.95, fontSize: 14, color: K.white, align: "center", valign: "middle" });
    T(s, "Thank you", { x: 0, y: 5.25, w: W, h: 0.8, fontSize: 40, fontFace: F.xbold, color: K.white, align: "center" });
    T(s, "Team LaMP  ·  Ishmam Tahmid  ·  Farhan Tahsin Khan", { x: 0, y: 6.15, w: W, h: 0.4, fontSize: 13, color: K.white, align: "center" });
  }

  const out = path.join(__dirname, "LaMP-Copilot.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
}

build().catch((e) => {
  console.error(e);
  process.exit(1);
});
