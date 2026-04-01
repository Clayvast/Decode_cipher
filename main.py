import math
import random
import re
from collections import Counter
import os
import urllib.request

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class CipherSolver:
    def ensure_quadgrams(self, filename):
        url = "https://raw.githubusercontent.com/jameslyons/python_cryptanalysis/master/quadgrams.txt"

        if os.path.exists(filename):
            return

        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print("Quadgrams downloaded successfully.")
        except Exception as e:
             raise RuntimeError(
            f"Failed to download quadgrams.txt.\n"
            f"Error: {e}\n"
            f"Please download manually from:\n{url}"
              )
    def __init__(self, cipher_file, quadgram_file="quadgrams.txt"):
         self.ensure_quadgrams(quadgram_file)
         self.ciphertext = self.read_file(cipher_file)
         self.quadgrams, self.floor = self.load_quadgrams(quadgram_file)
         self.locked = set()

    # --------------------------------------------------
    # File utilities
    # --------------------------------------------------

    def read_file(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().upper()

    def load_quadgrams(self, filename):
        quadgrams = {}
        total = 0

        with open(filename, "r") as f:
             for line in f:
                 line = line.strip()
                 if not line:
                     continue  # skip empty lines

                 parts = line.split()
                 if len(parts) != 2:
                     continue  # skip malformed lines

                 quad, count = parts
                 count = int(count)
                 quadgrams[quad] = count
                 total += count

             for quad in quadgrams:
                 quadgrams[quad] = math.log10(quadgrams[quad] / total)
    
             floor = math.log10(0.01 / total)
             return quadgrams, floor

    # --------------------------------------------------
    # Mapping utilities
    # --------------------------------------------------

    def random_mapping(self):
        shuffled = list(ALPHABET)
        random.shuffle(shuffled)
        return dict(zip(ALPHABET, shuffled))

    def apply_mapping(self, mapping):
        return "".join(mapping.get(c, c) if c.isalpha() else c for c in self.ciphertext)

    # --------------------------------------------------
    # Fitness scoring (quadgrams)
    # --------------------------------------------------

    def score(self, mapping):
        text = self.apply_mapping(mapping)
        filtered = "".join(c for c in text if c.isalpha())

        score = 0.0
        for i in range(len(filtered) - 3):
            quad = filtered[i:i+4]
            score += self.quadgrams.get(quad, self.floor)
        return score

    # --------------------------------------------------
    # Mapping mutation
    # --------------------------------------------------

    def swap(self, mapping):
        new = mapping.copy()
        letters = [c for c in ALPHABET if c not in self.locked]
        a, b = random.sample(letters, 2)
        new[a], new[b] = new[b], new[a]
        return new

    # --------------------------------------------------
    # Hill Climbing
    # --------------------------------------------------

    def hill_climb(self, mapping, iterations=3000):
        best = mapping
        best_score = self.score(mapping)

        for _ in range(iterations):
            trial = self.swap(best)
            s = self.score(trial)
            if s > best_score:
                best, best_score = trial, s

        return best, best_score

    # --------------------------------------------------
    # Simulated Annealing
    # --------------------------------------------------

    def simulated_annealing(self, mapping, steps=20000, temp=20.0):
        current = mapping
        current_score = self.score(current)

        best = current
        best_score = current_score

        for i in range(steps):
            temp *= 0.9995
            trial = self.swap(current)
            trial_score = self.score(trial)

            delta = trial_score - current_score
            if delta > 0 or random.random() < math.exp(delta / temp):
                current, current_score = trial, trial_score

                if current_score > best_score:
                    best, best_score = current, current_score
                    print(f"[+] New best @ {i} : {best_score:.2f}")

            if i % 2000 == 0:
                print(f"Iter {i} | Temp {temp:.2f} | Score {current_score:.2f}")

        return best, best_score

    # --------------------------------------------------
    # Manual editor
    # --------------------------------------------------

    def manual_editor(self, mapping):
        print("\nManual editor commands:")
        print("  A B        -> swap A and B")
        print("  LOCK A     -> lock letter")
        print("  UNLOCK A   -> unlock letter")
        print("  SHOW       -> preview text")
        print("  ENTER      -> finish\n")

        while True:
            cmd = input("Edit> ").strip().upper()
            if not cmd:
                break

            if cmd == "SHOW":
                print(self.apply_mapping(mapping)[:500])
                continue

            if cmd.startswith("LOCK"):
                _, l = cmd.split()
                self.locked.add(l)
                print(f"Locked {l}")
                continue

            if cmd.startswith("UNLOCK"):
                _, l = cmd.split()
                self.locked.discard(l)
                print(f"Unlocked {l}")
                continue

            try:
                a, b = cmd.split()
                mapping[a], mapping[b] = mapping[b], mapping[a]
                print(f"Score: {self.score(mapping):.2f}")
            except:
                print("Invalid command")

        return mapping

    # --------------------------------------------------
    # Full solve pipeline
    # --------------------------------------------------

    def solve(self):
        print("Starting solver...\n")

        mapping = self.random_mapping()

        print("Phase 1: Simulated Annealing")
        mapping, score = self.simulated_annealing(mapping)

        print("\nPhase 2: Hill Climb Cleanup")
        mapping, score = self.hill_climb(mapping)

        print("\nPhase 3: Manual Refinement")
        mapping = self.manual_editor(mapping)

        final = self.apply_mapping(mapping)
        final_score = self.score(mapping)

        print("\nFINAL SCORE:", final_score)
        print("="*50)
        print(final)
        print("="*50)

        with open("decrypted.txt", "w") as f:
            f.write(final)

        return final, mapping


# --------------------------------------------------
# Entry point
# --------------------------------------------------

def main():
    solver = CipherSolver("cipher.txt", "quadgrams.txt")
    solver.solve()


if __name__ == "__main__":
    main()