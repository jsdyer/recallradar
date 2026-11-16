# Recall Radar

Search Canadian recall and safety notices by text, issuer and archive status. Save search terms in this browser. The watchlist runs on visits and has no background notifications.

The static snapshot combines the English Health Canada [recalls and safety alerts dataset](https://open.canada.ca/data/dataset/d38de914-c94c-429b-8ab1-8776c31643e3) and the [Transport Canada 60-day vehicle recall dataset](https://open.canada.ca/data/dataset/1991fef6-9dfe-40e2-a0c6-19c60ddf4a02) under the Open Government Licence – Canada. Vehicle models are attached by exact recall number from a Transport Canada notice title. Supplemental rows with no corresponding Health Canada notice link to the official vehicle recall search. Only the supplied vehicle records carry model details. Official notices provide instructions and affected products.

```sh
python3 scripts/build.py
python3 -m http.server --directory dist 8000
```

Build using optional local files with `--health-file` and `--transport-file`. GitHub Actions refreshes the snapshot daily and supports manual dispatch. The prior deployment remains available if an official download or validation fails.
