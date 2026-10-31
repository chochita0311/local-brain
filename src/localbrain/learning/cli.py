"""Explicit reviewed-packet intake; never retrieves sources or executes models."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from localbrain.foundation.config import settings
from localbrain.persistence.db import connect, init_db
from localbrain.learning.service import LearningError, MAX_PACKET_BYTES, import_packet


def main(argv=None):
    parser = argparse.ArgumentParser(prog="localbrain learning")
    commands = parser.add_subparsers(dest="command", required=True)
    intake = commands.add_parser("import", help="Import a personally reviewed local lesson packet")
    intake.add_argument("path", type=Path)
    intake.add_argument("--reviewed", action="store_true", required=True,
                        help="Acknowledge that lesson claims and source snapshots were reviewed")
    args = parser.parse_args(argv)
    try:
        with args.path.open("rb") as stream:
            content = stream.read(MAX_PACKET_BYTES + 1)
        if len(content) > MAX_PACKET_BYTES:
            raise LearningError("패킷은 2 MiB 이하여야 합니다.")
        raw = json.loads(content)
        # Validate before startup or any content mutation.
        from localbrain.learning.service import today, validate_packet
        validate_packet(raw, today(settings.timezone_name))
        init_db()
        with closing(connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            result = import_packet(connection, raw, settings.timezone_name)
        print(json.dumps(result))
        return 0
    except LearningError as error:
        print(str(error))
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("패킷을 읽지 못했습니다. 파일과 JSON 형식을 확인해 주세요.")
    except sqlite3.Error:
        print("수업을 저장하지 못했습니다. DB 상태를 확인한 뒤 같은 패킷으로 다시 시도해 주세요.")
    return 2
