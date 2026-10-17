# Deck

- **`LaMP-Copilot.pptx`:** the 10-minute presentation (submission item 2), 25 slides.
- **`LaMP-Copilot.pdf`:** its PDF export, with fonts embedded.
- **`SPEAKER_NOTES.md`:** the talk script and per-slide timing, 9:30 in total. Notes are kept out of the slides on purpose.

The deck is generated, so edit `build-deck.js` and rebuild rather than editing the .pptx by hand:

```bash
cd deck
npm install
node build-deck.js
```

- **Look:** a copy of our earlier BCOLBD deck's visual language:
  - photo statement slides with red highlights
  - "▶ SECTION" headings
  - problem slides with a dashed core-issue box and lime symptom icons
  - a red core-issue slide
  - green step panels with cut-out people
  - dense slides with green-header tables
- **Images:**
  - `assets/bc/` holds icons and art reused from BCOLBD.
  - The photos (`pharmacy.jpg`, `counter.jpg`, `interior.jpg`, `bank.jpg`, `delivery.jpg`) and the cut-outs (`step-*.png`) also come from BCOLBD.
  - The two Vecteezy factory photos in BCOLBD are watermarked, so they are not used.
- **Font:** Poppins (free, Google Fonts). The PDF embeds it. To present the .pptx, install Poppins on that computer, or open it in Google Slides, which has Poppins built in. Otherwise PowerPoint swaps in another font.
- **Numbers:** must match the golden numbers in `docs/PLAN.md` section 6.
- **Screenshots:**
  - They are `assets/*-m.png`, taken from the running app after `POST /api/v1/dev/reset?with_demo_captures=true`.
  - Retake them if the UI changes.
- **Facts to verify before submitting:** slide 3 and slide 6 reuse market figures from the BCOLBD study that have no source in our docs. Those are $3.29B, >10.8% CAGR, 1.83% of GDP, 213 manufacturers, 98% local supply, BDT 1–3 lakh inventory, and CMSME lending to 27% by 2029.
