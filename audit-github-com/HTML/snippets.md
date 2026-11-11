# HTML snippets (public site only)

## `index.html` head template

```html
<!doctype html>
<html lang="en-GB">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#0c1211" />
    <title>LIN4CRE SENTINEL — Human-Controlled Security Research Operations</title>
    <meta name="description" content="Organise vulnerability research locally with exact-scope approvals, evidence-backed reports, verified recovery and human control. Open source; no autonomous submissions." />
    <link rel="canonical" href="https://sentinel.example.org/" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="manifest" href="/manifest.webmanifest" />
    <!-- Add OG/Twitter + JSON-LD from Metadata/ and Schema/ after replacing example origin. -->
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <header><a href="/" aria-label="LIN4CRE SENTINEL home">LIN4CRE SENTINEL</a><nav aria-label="Primary">...</nav></header>
    <main id="main"><h1>...</h1></main>
    <footer><nav aria-label="Footer">...</nav></footer>
  </body>
</html>
```

## Semantic 404 page

```html
<main id="main" class="not-found" aria-labelledby="not-found-title">
  <p class="eyebrow">404 · PAGE NOT FOUND</p>
  <h1 id="not-found-title">That page isn’t here.</h1>
  <p>Check the address or return to the SENTINEL home page.</p>
  <a class="button" href="/">Go to home</a>
  <a href="/docs/">Browse the documentation</a>
</main>
```

Serve the page with HTTP 404. Never return 200 for an unknown URL. Static site hosts need explicit 404 configuration; app router should have a not-found route while the server returns 404 where supported.
