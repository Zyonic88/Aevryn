# Aevryn Import Format Matrix

> Built by **Aetherra Labs**

This document tracks native source-format support for Story Import.

Rule:

Never claim source-format support until the parser is deterministic, tested,
and preserves evidence-anchor integrity.

All supported formats must enter the same Story Import parser after adapter
normalization.

Adapters prepare text.

Story Import owns chapter parsing, scene splitting, paragraph indexing,
sentence indexing, and evidence anchors.

---

# V1.1 Supported Formats

| Format | Adapter Owner | Evidence-Anchor Status | Notes |
| --- | --- | --- | --- |
| TXT | SourceFileTextExtractor | Supported | Read as UTF-8 text and passed directly to Story Import. |
| Markdown | SourceFileTextExtractor | Supported | Read as UTF-8 text; Markdown markers remain source text. |
| HTML/XHTML | SourceFileTextExtractor | Supported | Extracts visible text and skips script, style, and navigation blocks. |
| FB2 | SourceFileTextExtractor | Supported | Extracts paragraph-like XML text from FictionBook files. |
| DOCX | SourceFileTextExtractor | Supported | Extracts paragraph text from `word/document.xml`. |
| ODT | SourceFileTextExtractor | Supported | Extracts heading and paragraph text from `content.xml`. |
| EPUB | EpubTextExtractor | Supported | Extracts readable spine content and removes navigation-only material. |

---

# Deferred Formats

| Format | Status | Reason |
| --- | --- | --- |
| PDF | Deferred | Requires a deterministic PDF text parser that preserves reading order. |
| MOBI | Deferred | Requires a dedicated Kindle parser dependency. |
| AZW3 | Deferred | Requires a dedicated Kindle parser dependency. |

Deferred formats must fail clearly until parser support is implemented and tested.

---

# Acceptance Requirements

A format becomes supported only when it satisfies:

* Deterministic text extraction
* Clear malformed-file errors
* Unicode preservation
* Stable Story Import counts on repeated imports
* Evidence anchors that point to extracted sentence text
* Tests for successful import
* Tests for malformed or unsupported input
* Documentation in this matrix

If any requirement is missing, the format remains deferred.
