import os
import stat

_Signature = tuple[int, int, float]

PWDS_PATH = "secrets/passwords.txt"
_cache: tuple[_Signature, dict[str, str]] | None = None

def hashed_passwords() -> dict[str, str]:
    global _cache

    sig = _signature(PWDS_PATH)
    if _cache is not None and _cache[0] == sig:
        return _cache[1]
    
    value = {}
    with open(PWDS_PATH, "r") as file:
        for line in file:
            [username, hashed_password] = line.rstrip().split(" ", 1)
            value[username] = hashed_password
    _cache = (sig, value)
    return value

def _signature(path: str) -> _Signature:
    st = os.stat(path)
    return (stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime)
