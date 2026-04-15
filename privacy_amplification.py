import hashlib

def apply_privacy_amplification(key_bits):
    # Transformăm lista [0, 1, 1...] în string "011..."
    key_str = "".join(map(str, key_bits))
    # Generăm un hash SHA-256 (rezultat hexazecimal)
    return hashlib.sha256(key_str.encode()).hexdigest()