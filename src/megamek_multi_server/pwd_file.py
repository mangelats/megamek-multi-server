import os
import stat

_Signature = tuple[int, int, float]
_cache: tuple[_Signature, dict[str, str]] | None = None


def hashed_password(username: str) -> str | None:
    if not username:
        return None
    return _hashed_passwords().get(username)


def _hashed_passwords() -> dict[str, str]:
    global _cache
    pwds_path = os.environ["MEGAMEK_MULTI_SERVER_PASSWORDS"]

    sig = _signature(pwds_path)
    if _cache is not None and _cache[0] == sig:
        return _cache[1]

    value = {}
    with open(pwds_path, "r") as file:
        for line in file:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue
            [username, hashed_password] = line.rstrip().split(" ", 1)
            value[username] = hashed_password
    _cache = (sig, value)
    return value


def _signature(path: str) -> _Signature:
    """Computes a unique signature for a path state."""
    st = os.stat(path)
    return (stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime)
