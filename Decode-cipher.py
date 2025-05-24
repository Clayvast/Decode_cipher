from typing import List, Dict
from copy import deepcopy
import time
from functools import lru_cache

# Memoized version of is_consistent
@lru_cache(maxsize=None)
def is_consistent_cached(cipher_word: str, candidate_word: str, mapping_items: tuple) -> bool:
    mapping = dict(mapping_items)
    used_plain_letters = set(mapping.values())

    for c_cipher, c_plain in zip(cipher_word, candidate_word):
        if c_cipher in mapping:
            if mapping[c_cipher] != c_plain:
                return False
        else:
            if c_plain in used_plain_letters:
                return False  # Enforce one-to-one mapping
            mapping[c_cipher] = c_plain
            used_plain_letters.add(c_plain)

    return True

def apply_mapping(cipher_word: str, mapping: Dict[str, str]) -> str:
    return ''.join(mapping.get(c, '?') for c in cipher_word)

def has_future_conflicts(index: int, cipher_text: List[str], suitable_subs: List[List[str]], mapping: Dict[str, str]) -> bool:
    for i in range(index + 1, len(cipher_text)):
        cipher_word = cipher_text[i]
        if not any(is_consistent_cached(cipher_word, candidate, tuple(mapping.items()))
                   for candidate in suitable_subs[i]):
            return True  # No valid candidates ahead
    return False

def find_all_valid_mappings(index: int, cipher_text: List[str], suitable_subs: List[List[str]],
                            current_mapping: Dict[str, str], all_mappings: List[Dict[str, str]],
                            last_report_time: List[float]):
    if index == len(cipher_text):
        all_mappings.append(deepcopy(current_mapping))
        return

    cipher_word = cipher_text[index]
    for candidate in suitable_subs[index]:
        current_time = time.time()
        if current_time - last_report_time[0] >= 10:
            print(f"⏳ Still working... Trying word #{index + 1}/{len(cipher_text)}: '{cipher_word}' → '{candidate}'")
            print(f"   Current mapping so far: {current_mapping}")
            last_report_time[0] = current_time

        if is_consistent_cached(cipher_word, candidate, tuple(current_mapping.items())):
            extended_mapping = current_mapping.copy()
            for c_ciph, c_plain in zip(cipher_word, candidate):
                extended_mapping[c_ciph] = c_plain

            if not has_future_conflicts(index, cipher_text, suitable_subs, extended_mapping):
                find_all_valid_mappings(index + 1, cipher_text, suitable_subs, extended_mapping, all_mappings, last_report_time)

# === Input and setup ===

length_of_cipher = int(input("How many words does your cipher text have? "))
cipher_text = [input(f"Please input cipher word #{i+1}: ") for i in range(length_of_cipher)]

# Load common words from file
try:
    with open("lots_of_words.txt", "r", encoding="utf-8") as f:
        common_words = [line.strip().lower() for line in f if line.strip()]
except FileNotFoundError:
    print("❌ Error: 'lots_of_words.txt' not found.")
    common_words = []

# Find candidate substitutions by word length
suitable_sub = [[] for _ in range(length_of_cipher)]
for i, word in enumerate(cipher_text):
    unique_letters = len(set(word))
    for common_word in common_words:
        if len(common_word) == len(word) and len(set(common_word)) == unique_letters:
            suitable_sub[i].append(common_word)

# Sort cipher words by number of candidates (Minimum Remaining Values)
indexed = list(zip(cipher_text, suitable_sub))
indexed.sort(key=lambda x: len(x[1]))
cipher_text, suitable_sub = zip(*indexed)
cipher_text = list(cipher_text)
suitable_sub = list(suitable_sub)

# Find all valid mappings
all_mappings = []
last_report_time = [time.time()]
find_all_valid_mappings(0, cipher_text, suitable_sub, {}, all_mappings, last_report_time)

# Output results
if all_mappings:
    print(f"\n✅ Found {len(all_mappings)} consistent mapping(s):")
    for i, mapping in enumerate(all_mappings, 1):
        print(f"\nMapping #{i}:")
        for k, v in sorted(mapping.items()):
            print(f"  {k} -> {v}")
        print("Decrypted Text:", ' '.join(apply_mapping(word, mapping) for word in cipher_text))
else:
    print("\n❌ No consistent mapping could be found.")
