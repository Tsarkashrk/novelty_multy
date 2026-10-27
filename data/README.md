# Topic archive provenance

`openalex_thesis_topics.csv` was copied from the user-provided OpenAlex silver dataset in the local `novelty-similarity-detection-model` project. The file has 230 topic records: 160 metadata records from OpenAlex and 70 controlled synthetic variants derived from those records. It also contains source IDs, URLs, language, year, and domain metadata. The original project's `data/openalex_silver/README.md` describes its collection and silver-label construction.

The multi-agent application reads all rows, validates IDs and required columns, and by default excludes the 70 records marked `is_synthetic=true` from novelty and duplication decisions. `--include-synthetic` includes them for benchmark demonstrations. Results link to the OpenAlex record where the URL is present.

The archive is a limited research sample; a low lexical overlap with these records does not prove academic novelty. Synthetic variants are generated examples, not independent university theses. The separate `archive_topics.json` file is a small demonstration archive and is used only with `--archive-source sample`.
