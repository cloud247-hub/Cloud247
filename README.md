Cloud247.no bilingual GitHub Pages build. Norwegian and English language switcher with saved preference.

## Blogg

Innleggene skrives i Markdown i `blogg-kilde/` og bygges til `blogg/` med:

    pip install markdown
    python3 scripts/build-blog.py

Skriptet lager én HTML-fil per innlegg (`blogg/<slug>.html`, servert som `/blogg/<slug>`), forsiden `blogg/index.html` og oppdaterer `sitemap.xml`.
