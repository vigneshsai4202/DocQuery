from app.services.chunking import TextChunk, chunk_pages


def test_basic_chunking():
    # Use text with sentence boundaries so the sentence splitter can split it
    sentences = [f"This is sentence number {i} in the test document." for i in range(50)]
    pages = {1: " ".join(sentences)}
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    for c in chunks:
        assert isinstance(c, TextChunk)
        assert c.page_number == 1
        assert c.text.strip()


def test_overlap_produces_shared_words():
    words = [f"w{i}" for i in range(100)]
    pages = {1: " ".join(words)}
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)
    if len(chunks) >= 2:
        end_words = set(chunks[0].text.split()[-10:])
        start_words = set(chunks[1].text.split()[:10])
        assert end_words & start_words, "Expected overlapping words between consecutive chunks"


def test_multi_page_preserves_page_numbers():
    pages = {
        1: " ".join([f"p1w{i}" for i in range(100)]),
        2: " ".join([f"p2w{i}" for i in range(100)]),
    }
    chunks = chunk_pages(pages, chunk_size=50, overlap=5)
    page_nums = {c.page_number for c in chunks}
    assert 1 in page_nums
    assert 2 in page_nums


def test_empty_page_skipped():
    pages = {1: "", 2: "hello world this is a test sentence with enough words to form a chunk properly here"}
    chunks = chunk_pages(pages, chunk_size=10, overlap=2)
    assert all(c.page_number == 2 for c in chunks)


def test_chunk_indices_are_sequential():
    pages = {1: " ".join([f"word{i}" for i in range(300)])}
    chunks = chunk_pages(pages, chunk_size=50, overlap=5)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(indices)))
