# -*- coding: utf-8 -*-
import time
import threading
from pathlib import Path
import pytest

from src.utils.file_lock import InterProcessFileLock, FileLockTimeoutError


def test_file_lock_acquire_and_release(tmp_path: Path):
    lock_file = tmp_path / "test.lock"
    lock = InterProcessFileLock(lock_file, timeout=2.0)
    
    assert not lock._acquired
    with lock:
        assert lock._acquired
        assert lock_file.exists()
    assert not lock._acquired


def test_file_lock_contention_timeout(tmp_path: Path):
    lock_file = tmp_path / "test_timeout.lock"
    lock1 = InterProcessFileLock(lock_file, timeout=1.0)
    lock2 = InterProcessFileLock(lock_file, timeout=0.3)
    
    lock1.acquire()
    try:
        with pytest.raises(FileLockTimeoutError):
            lock2.acquire()
    finally:
        lock1.release()

    # Après libération, lock2 peut maintenant acquérir
    with lock2:
        assert lock2._acquired


def test_file_lock_multithreading(tmp_path: Path):
    lock_file = tmp_path / "test_threads.lock"
    shared_counter = []

    def worker(val):
        with InterProcessFileLock(lock_file, timeout=5.0):
            current = len(shared_counter)
            time.sleep(0.01)
            shared_counter.append(current)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(shared_counter) == 5
    assert shared_counter == list(range(5))
