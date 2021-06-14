import pytest

@pytest.fixture
def english_words_small():
    return set((
"open",
"peon",
"nope",
"stone",
"notes",
"onset",
"tones",
"cone",
"pots",
"post",
"stop",
"opts",
"tops",
))

@pytest.fixture
def english_anagrams_small():
    return {
    "enop": {"open", "peon", "nope"},
    "enost": {"stone", "notes", "onset", "tones"},
    "ceno": {"cone"},
    "opst": {"pots", "post", "stop", "opts", "tops"}
}