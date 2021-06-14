import pytest

from handbook.utils import common
from tests.helpers import english_words_small, english_anagrams_small

@pytest.mark.parametrize(
    "dictionary",
    [
        {"one": 1, "two": 2, "three": 3},
        {"one": 1, "two": 2, "three": [3, 4]}
    ]
)
def test_swap_keys_and_values(dictionary):
    new_d = common.swap_keys_and_values(dictionary)
    old_values = set(common.flatten_sequence(dictionary.values()))
    new_values = set(common.flatten_sequence(new_d.values()))
    new_keys = set(common.flatten_sequence(new_d.keys()))
    assert all(k in new_values for k in dictionary)
    assert all(v in new_keys for v in old_values)
