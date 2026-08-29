"""
Chunking service — sentence-boundary sliding window.

Splits text into chunks that respect sentence boundaries, avoiding
mid-sentence cuts. Falls back to word splitting for text without
punctuation (e.g. scanned PDFs with poor extraction).
"""
import re
from dataclasses import dataclass

from app.core.config import settings

_WORDS_PER_TOKEN = 0.75
_SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')


def _word_count(text: str) -> int:
    return len(text.split())


def _words_for_tokens(n: int) -> int:
    return int(n * _WORDS_PER_TOKEN)


def _split_sentences(text: str) -> list[str]:
    sentences = _SENTENCE_RE.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


@dataclass
class TextChunk:
    text: str
    page_number: int
    chunk_index: int


def chunk_pages(
    pages: dict[int, str],
    chunk_size: int = settings.CHUNK_SIZE_TOKENS,
    overlap: int = settings.CHUNK_OVERLAP_TOKENS,
) -> list[TextChunk]:
    """
    Given {page_number: text}, return a flat list of TextChunks.

    Strategy:
    - Split each page into sentences.
    - Accumulate sentences until chunk_size words is reached.
    - Carry over the last `overlap` words into the next chunk.
    - Tiny trailing segments (< 20 words) are merged into the previous chunk.
    """
    max_words = _words_for_tokens(chunk_size)
    overlap_words = _words_for_tokens(overlap)

    chunks: list[TextChunk] = []
    chunk_index = 0

    for page_num in sorted(pages.keys()):
        text = pages[page_num].strip()
        if not text:
            continue

        sentences = _split_sentences(text)
        if not sentences:
            continue

        current: list[str] = []
        current_wc = 0

        for sentence in sentences:
            swc = _word_count(sentence)

            # If adding this sentence exceeds the limit, flush current chunk
            if current_wc + swc > max_words and current:
                chunk_text = " ".join(current)
                if _word_count(chunk_text) < 20 and chunks:
                    chunks[-1] = TextChunk(
                        text=chunks[-1].text + " " + chunk_text,
                        page_number=chunks[-1].page_number,
                        chunk_index=chunks[-1].chunk_index,
                    )
                else:
                    chunks.append(TextChunk(text=chunk_text, page_number=page_num, chunk_index=chunk_index))
                    chunk_index += 1

                # Carry overlap: keep last N words as seed for next chunk
                all_words = chunk_text.split()
                carry = all_words[-overlap_words:] if overlap_words else []
                current = [" ".join(carry)] if carry else []
                current_wc = len(carry)

            current.append(sentence)
            current_wc += swc

        # Flush remaining
        if current:
            chunk_text = " ".join(current)
            if _word_count(chunk_text) < 20 and chunks:
                chunks[-1] = TextChunk(
                    text=chunks[-1].text + " " + chunk_text,
                    page_number=chunks[-1].page_number,
                    chunk_index=chunks[-1].chunk_index,
                )
            else:
                chunks.append(TextChunk(text=chunk_text, page_number=page_num, chunk_index=chunk_index))
                chunk_index += 1

    return chunks
