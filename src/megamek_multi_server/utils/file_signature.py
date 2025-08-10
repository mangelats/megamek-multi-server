import os
import stat


class Signature:
    """Signature of a file. Useful to detect if a file changed."""

    _inner: tuple[int, int, float]

    @staticmethod
    def for_file(path: str) -> "Signature":
        s = Signature()
        s._inner = _signature(path)
        return s

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Signature):
            return self._inner == other._inner
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self._inner)


def _signature(path: str) -> tuple[int, int, float]:
    """Computes a unique signature for a path state. Any will change it."""
    st = os.stat(path)
    return (stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime)
