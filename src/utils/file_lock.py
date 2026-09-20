# -*- coding: utf-8 -*-
"""
Portable Inter-Process File Lock (mLoop Core).

Verrou consultatif inter-processus et inter-thread compatible Windows et Unix :
- Windows : msvcrt.locking
- Unix / macOS : fcntl.flock
- Mutex de thread local pour éliminer les contentions intra-processus.
- Support de timeout avec réessais progressifs.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("file_lock")


class FileLockTimeoutError(TimeoutError):
    """Levée lorsqu'un verrou de fichier ne peut pas être acquis dans le délai imparti."""


_LOCAL_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.Lock] = {}


def _get_canonical_key(path: Path) -> str:
    """Retourne la clé canonique normalisée pour le verrou intra-processus."""
    return os.path.normcase(str(path.expanduser().resolve(strict=False)))


def _get_local_thread_lock(path: Path) -> threading.Lock:
    """Obtient ou crée un verrou de thread pour le chemin spécifié."""
    key = _get_canonical_key(path)
    with _LOCAL_LOCKS_GUARD:
        if key not in _LOCAL_LOCKS:
            _LOCAL_LOCKS[key] = threading.Lock()
        return _LOCAL_LOCKS[key]


def _try_os_lock(fd: int) -> bool:
    """Tente d'acquérir le verrou OS en mode non-bloquant."""
    if sys.platform == "win32":
        import msvcrt

        try:
            # Revenir au début du fichier et verrouiller 1 octet
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except (OSError, IOError):
            return False
    else:
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (OSError, IOError):
            return False


def _unlock_os_lock(fd: int) -> None:
    """Libère le verrou OS."""
    if sys.platform == "win32":
        import msvcrt

        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except (OSError, IOError) as e:
            logger.debug(
                "Déverrouillage OS (Windows) ignoré",
                exc_info=True,
                extra={"fd": fd, "error": str(e)},
            )
    else:
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except (OSError, IOError) as e:
            logger.debug(
                "Déverrouillage OS (Unix) ignoré",
                exc_info=True,
                extra={"fd": fd, "error": str(e)},
            )


class InterProcessFileLock:
    """
    Verrou de fichier inter-processus et inter-thread réentrant au niveau processus
    via un mutex de thread local et un descripteur de fichier OS.
    """

    def __init__(self, lock_path: str | Path, timeout: float = 10.0) -> None:
        self.path = Path(lock_path).expanduser().resolve(strict=False)
        self.timeout = float(timeout)
        if self.timeout < 0:
            raise ValueError("Le timeout ne peut pas être négatif")

        self.pid = os.getpid()
        self.token = uuid.uuid4().hex
        self._acquired = False
        self._fd: Optional[int] = None
        self._thread_lock: Optional[threading.Lock] = None

    def acquire(self) -> "InterProcessFileLock":
        """Acquiert le verrou ou lève FileLockTimeoutError."""
        if self._acquired:
            raise RuntimeError(f"Le verrou {self.path} est déjà acquis par cette instance")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout

        # 1. Acquérir le verrou de thread local
        thread_lock = _get_local_thread_lock(self.path)
        while not thread_lock.acquire(blocking=False):
            if time.monotonic() >= deadline:
                raise FileLockTimeoutError(
                    f"Délai dépassé ({self.timeout}s) pour acquérir le verrou de thread sur {self.path}"
                )
            time.sleep(min(0.05, max(0.005, deadline - time.monotonic())))
        self._thread_lock = thread_lock

        # 2. Ouvrir le fichier et acquérir le verrou OS
        try:
            flags = os.O_CREAT | os.O_RDWR
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            self._fd = os.open(str(self.path), flags, 0o666)

            # S'assurer qu'au moins 1 octet existe dans le fichier
            if os.fstat(self._fd).st_size == 0:
                os.write(self._fd, b"0")
                os.fsync(self._fd)

            while not _try_os_lock(self._fd):
                if time.monotonic() >= deadline:
                    raise FileLockTimeoutError(
                        f"Délai dépassé ({self.timeout}s) pour acquérir le verrou OS sur {self.path}"
                    )
                time.sleep(min(0.05, max(0.005, deadline - time.monotonic())))

            self._acquired = True
            return self
        except BaseException:
            self._cleanup_failed_acquisition()
            raise

    def release(self) -> None:
        """Libère le verrou OS et le verrou de thread."""
        if not self._acquired:
            return

        self._acquired = False
        try:
            if self._fd is not None:
                _unlock_os_lock(self._fd)
                try:
                    os.close(self._fd)
                except OSError as e:
                    logger.debug(
                        "Fermeture du descripteur (release) ignorée",
                        exc_info=True,
                        extra={"fd": self._fd, "path": str(self.path), "error": str(e)},
                    )
                self._fd = None
        finally:
            if self._thread_lock is not None:
                self._thread_lock.release()
                self._thread_lock = None

    def _cleanup_failed_acquisition(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError as e:
                logger.debug(
                    "Fermeture du descripteur (cleanup) ignorée",
                    exc_info=True,
                    extra={"fd": self._fd, "path": str(self.path), "error": str(e)},
                )
            self._fd = None
        if self._thread_lock is not None:
            self._thread_lock.release()
            self._thread_lock = None

    def __enter__(self) -> "InterProcessFileLock":
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
