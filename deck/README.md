# Deck

`LaMP-Copilot.pptx` is the 10-minute presentation (15 slides) (submission item 2). Each slide has speaker notes with a time target, about 9:50 in total. `LaMP-Copilot.pdf` is the PDF export.

The deck is generated, so edit `build-deck.js` and rebuild rather than editing the .pptx by hand:

```bash
cd deck
npm install
node build-deck.js
```

- **Look:** follows our earlier BCOLBD deck: deep pharmacy green, mint cards, bold sans headings. Fonts are Arial so it renders the same everywhere.
- **Numbers:** must match the golden numbers in `docs/PLAN.md` section 6.
- **Screenshots:** in `assets/`, taken from the running app after `POST /api/v1/dev/reset?with_demo_captures=true`. Retake them if the UI changes.
- **Title photo:** `assets/pharmacy.jpg`, from the BCOLBD deck.
