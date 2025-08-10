from typing import TypeVar

from werkzeug.security import check_password_hash, generate_password_hash

from megamek_multi_server.utils.file_signature import Signature

_DEFAULT_PASSWORD = generate_password_hash("")


class FileAuth:
    """User logging from a password file."""

    _path: str
    _cache: tuple[Signature, dict[str, str]]

    def __init__(self, path: str):
        self._path = path
        self._update_cache(None)

    def check_password(self, username: str, password: str) -> bool:
        """Gets the password hash of a user."""
        if not username or not password:
            return False

        password_hash = self._entries().get(username)

        # Security: It's important to NOT return early. Doing so would leak all
        #   the usernames with a timming attack (real users would take time to
        #   verify the password but if the user does not exist it would end
        #   faster because less work would be done).
        #   `werkzeug.security` is not doing a good job avoiding this attack.
        hash = _default(password_hash, _DEFAULT_PASSWORD)
        password_valid = check_password_hash(hash, password)

        # At this point the time to check the password has been done.
        # Note that `password_hash is not None` is necessary just in case
        # somebody uses the same password as `_DEFAULT_PASSWORD`.
        return password_hash is not None and password_valid

    def _entries(self) -> dict[str, str]:
        sig = Signature.for_file(self._path)
        if self._cache[0] != sig:
            self._update_cache(sig)
        return self._cache[1]

    def _update_cache(self, sig: Signature | None) -> None:
        if sig is None:
            sig = Signature.for_file(self._path)
        self._cache = (sig, _deserialize(self._path))


T = TypeVar("T")


def _default(v: T | None, default: T) -> T:
    if v is None:
        return default
    else:
        return v


def _deserialize(path: str) -> dict[str, str]:
    """Reads a path and deserialize the username - password hash pairs."""
    value = {}
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            [username, hashed_password] = line.rstrip().split(" ", 1)
            value[username] = hashed_password
    return value
