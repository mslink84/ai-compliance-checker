"""Tests for document chunking logic in analyzer.py."""

import pytest

from analyzer import MAX_DOC_CHARS, OVERLAP_CHARS, _split_into_chunks


def test_short_document_is_single_chunk():
    text = "a" * (MAX_DOC_CHARS - 1)
    chunks = _split_into_chunks(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_document_at_exact_limit_is_single_chunk():
    text = "a" * MAX_DOC_CHARS
    chunks = _split_into_chunks(text)
    assert len(chunks) == 1


def test_document_over_limit_produces_multiple_chunks():
    text = "a" * (MAX_DOC_CHARS + 1)
    chunks = _split_into_chunks(text)
    assert len(chunks) == 2


def test_chunks_cover_entire_document():
    """Every character in the original document must appear in at least one chunk."""
    text = "abcdefghij" * 3000  # 30,000 chars → several chunks
    chunks = _split_into_chunks(text)
    assert len(chunks) > 1
    # First chunk starts at the beginning
    assert chunks[0] == text[: MAX_DOC_CHARS]
    # Last chunk ends at the document end
    assert text.endswith(chunks[-1])


def test_chunks_overlap():
    """Adjacent chunks share OVERLAP_CHARS characters (to avoid cutting mid-sentence)."""
    text = "x" * (MAX_DOC_CHARS * 2)
    chunks = _split_into_chunks(text)
    assert len(chunks) >= 2
    # End of first chunk should match start of second chunk
    assert chunks[0][-OVERLAP_CHARS:] == chunks[1][:OVERLAP_CHARS]


def test_each_chunk_not_larger_than_max():
    text = "w" * (MAX_DOC_CHARS * 5)
    for chunk in _split_into_chunks(text):
        assert len(chunk) <= MAX_DOC_CHARS
