"""Read process identity and POSIX session membership without command contents."""
import json
import os
import subprocess


def process_table():
    output = subprocess.check_output(
        ["/bin/ps", "-axo", "pid=,ppid=,pgid=,lstart=,stat="], text=True, timeout=2)
    records = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 9:
            continue
        pid = int(fields[0])
        if pid <= 1:
            continue
        try:
            session = os.getsid(pid)
        except ProcessLookupError:
            continue
        except PermissionError:
            session = None  # Session IDs from other users cannot establish ownership.
        records.append({"pid": pid, "parent": int(fields[1]), "group": int(fields[2]),
                        "session": session, "born": " ".join(fields[3:8]), "dead": "Z" in fields[8]})
    return records


if __name__ == "__main__":
    print(json.dumps(process_table()))
