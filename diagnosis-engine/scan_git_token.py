"""Scan tracked working files and reachable Git blobs for an exact token.
Run on Windows in the do-an repository. No token/blob content is printed.
This cannot certify absence of old unknown credentials or remote/deleted refs.
"""
import getpass
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.run(['git',*args],check=True,capture_output=True).stdout


def main():
    root=Path(git('rev-parse','--show-toplevel').decode().strip())
    token=getpass.getpass('Current API token (hidden; Enter to cancel): ').strip()
    if not token:
        print('Cancelled; nothing scanned.');return
    needle=token.encode()
    tracked=git('ls-files','--full-name','-z').split(b'\0')
    work_hits=0
    for raw in tracked:
        if raw:
            path=root/raw.decode('utf-8',errors='surrogateescape')
            if path.is_file() and needle in path.read_bytes():work_hits+=1
    object_ids={line.split(b' ',1)[0] for line in git('rev-list','--objects','--all').splitlines()}
    history_hits=0
    for oid in object_ids:
        name=oid.decode('ascii')
        if git('cat-file','-t',name).strip()==b'blob' and needle in git('cat-file','blob',name):
            history_hits+=1
    env_tracked=any(raw and Path(raw.decode()).name=='.env' for raw in tracked)
    print('Tracked working files containing exact token:',work_hits)
    print('Reachable historical blobs containing exact token:',history_hits)
    print('.env currently tracked:',env_tracked)
    if work_hits or history_hits or env_tracked:
        raise SystemExit('REVIEW REQUIRED: do not push; revoke exposed token if present.')
    print('PASS for this exact token only; inspect any previous tokens separately.')


if __name__=='__main__':
    main()
