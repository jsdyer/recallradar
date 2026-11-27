# Recall Radar

<!-- coolcode:guide -->
Browse product topics to check the latest updated notices, or select a category and search for a product or brand. Save a search term, then revisit to check matching notices and read the issuing agency’s instructions. The watchlist runs when you visit and does not send background notifications.
<!-- /coolcode:guide -->

Search Canadian recall and safety notices by text, issuer and archive status. Save search terms in this browser. The watchlist runs on visits and has no background notifications.

The static snapshot combines the English Health Canada [recalls and safety alerts dataset](https://open.canada.ca/data/dataset/d38de914-c94c-429b-8ab1-8776c31643e3) and the [Transport Canada 60-day vehicle recall dataset](https://open.canada.ca/data/dataset/1991fef6-9dfe-40e2-a0c6-19c60ddf4a02) under the Open Government Licence – Canada. Vehicle models are attached by exact recall number from a Transport Canada notice title. Supplemental rows with no corresponding Health Canada notice link to the official vehicle recall search. Only the supplied vehicle records carry model details. Official notices provide instructions and affected products.

```sh
python3 scripts/build.py
python3 -m http.server --directory dist 8000
```

Build using optional local files with `--health-file` and `--transport-file`. GitHub Actions refreshes the snapshot daily and supports manual dispatch. The prior deployment remains available if an official download or validation fails.

The [snapshot metadata](https://coolcode.ca/recallradar/data-status.json) gives the retrieval timestamp, snapshot build date, record count, number of matched vehicle notices, and latest update recorded in the vehicle feed. Builds using saved input files leave the retrieval timestamp empty.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

The separate schedule guard remains a mitigation, not a scheduling guarantee. The independent [CoolCode refresh watchdog](https://github.com/jsdyer/jsdyer.github.io/blob/main/services/refresh-watchdog/README.md) is maintained in GitHub and uses the generated workflow and freshness registry; do not maintain another target list here. Using it requires installation on a Linux server and GitHub credentials with access to this repository. A generated target does not prove that a private server has adopted it; verify the installed service's report. The guard does not collect data, create dummy commits or change source/check timestamps. Successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->

## Consumer product topics

The [topic directory](https://coolcode.ca/recallradar/records/) groups notices under Health Canada’s own category labels. Each topic lists the twelve most recently updated non-archived notices. The search link opens the same complete category with brand, product and archive filters. A notice can appear in several groups. A topic appears in the result sitemap when its snapshot contains at least one notice. The existing daily workflow rebuilds these pages from the same source downloads. Edit `web/product-topics.json` to add another exact category label from the export.

## Ready-to-use searches

- [Ford F-150 Recalls in Canada](https://coolcode.ca/recallradar/ford-f150.html). See notices with an exact Ford F-150 model entry in the retained Transport Canada data. Choose a model year to narrow the list. Open the official notice to confirm applicable vehicles and repair instructions.
- [Ford Escape Recalls in Canada](https://coolcode.ca/recallradar/ford-escape.html). Review Ford Escape safety notices and the model years listed by Transport Canada. Recent joined records include model details. For a complete history or an individual vehicle, follow the official recall and manufacturer VIN lookup guidance.
