from ai_lab.utils import split_text

def test_split_text_basic():
    txt = " ".join(["word"]*5000)
    chunks = split_text(txt, max_chars=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 1500 for c in chunks)
