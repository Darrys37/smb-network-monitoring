"""Bounded demo guard: the same byte locks as existing coordinators, plus wake."""
from contextlib import ExitStack, contextmanager
from pathlib import Path
import os
import threading

LOCK_NAMES = ("ml-supervisor.lock", "ml-acceptance.lock")


@contextmanager
def byte_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.lockf(stream, fcntl.LOCK_EX | fcntl.LOCK_NB, 1, 0)
        except OSError as error:
            raise RuntimeError("Lab is busy: " + path.name) from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.lockf(stream, fcntl.LOCK_UN, 1, 0)


@contextmanager
def keep_awake():
    if os.name != "nt":
        yield
        return
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    wake = kernel.SetThreadExecutionState
    wake.argtypes = [ctypes.c_uint]
    wake.restype = ctypes.c_uint
    if not wake(0x80000003):
        raise OSError("Cannot establish temporary display/system wake request")
    stop = threading.Event()
    errors = []

    def refresh():
        try:
            while not stop.wait(15):
                if not wake(0x80000003):
                    errors.append("Cannot renew temporary wake request")
        finally:
            wake(0x80000000)

    worker = threading.Thread(target=refresh, name="lab-wake-request", daemon=True)
    try:
        worker.start()
        yield
        if errors:
            raise RuntimeError(errors[0])
    finally:
        stop.set()
        if worker.ident is not None:
            worker.join(timeout=2)
        wake(0x80000000)


@contextmanager
def lab_session(coordination_root):
    with ExitStack() as stack:
        for name in LOCK_NAMES:
            stack.enter_context(byte_lock(Path(coordination_root) / "verification" / name))
        stack.enter_context(keep_awake())
        yield
