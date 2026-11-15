# Real Progress Sans font files

`ProgressSansDisplayVF.woff2` and `ProgressSansTextVF.woff2` are the genuine variable
fonts served by www.progress.com, pulled on 29 Sep 2026 with
`hyperframes capture https://www.progress.com/agentic-rag` (they land in the capture's
`assets/fonts/`). Both carry a `wght` axis (100-900); the Text face also has `slnt`.

Why they are here: HyperFrames rewrites every system font through a hardcoded alias map,
so declaring `font-family: Arial` silently renders **Inter** fetched from Google Fonts.
The only way to control the rendered typeface - and the only air-gap-safe way - is a local
`@font-face` pointing at a real file, under a family name that is not in the alias map.
Wired that way these render genuine Progress Sans. See the `hyperframes-video` skill,
section 3.

```css
@font-face {
  font-family: "ProgressSansDisplay";
  src: url("assets/ProgressSansDisplayVF.woff2") format("woff2");
  font-weight: 100 900; font-style: normal; font-display: block;
}
```

Progress's own fonts, used for Progress's own marketing videos. Not for redistribution
outside that.

## Position on the Prepare (seller) shell of apps/forge-co (GM, 23 Oct 2026; supersedes an earlier entry)

**The app REFERENCES Progress's own host and serves no copy.** The GM: "change to progress owned host if easiest. as
i work for progress, no problem getting the files." That replaces the earlier decision to ship copies from the app's
own host, and with it the licensing question: nothing is redistributed, the page loads the files from the same
CloudFront origin www.progress.com loads them from.

- URLs: `https://d6vtbcy3ong79.cloudfront.net/fonts/latest/progress/Display.woff2` and `.../Text.woff2`, read from the
  `@font-face` rules in https://www.progress.com/agentic-rag's stylesheet, with its own declarations
  (`format("woff2-variations")`, Display `font-weight: 400 700`, Text `100 700`).
- **Measured 23 Oct 2026 before shipping** (a cross-origin webfont without CORS is silently substituted, so it was tested,
  not assumed): both answer 200 with `access-control-allow-origin: *`, `content-type: font/woff2` and 30 days of cache,
  and are byte-identical (md5) to the two files in this directory. In a browser from a different origin both faces report
  `loaded` and the variable axis moves (Text 489.6px at weight 300, 519.6px at 700, against 451.1px for system-ui).
- **Risks, stated.** The page now depends on that host being reachable from wherever it is opened; if it is not,
  `font-display: swap` shows the system-ui fallback with the same layout and nothing breaks. The path contains `/latest/`,
  so Progress can change the files under the app; re-run the measurement above if the type ever looks different.
- The copies in this directory remain the source for video work (see above); the app keeps none.
