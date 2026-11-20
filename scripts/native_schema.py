"""Read the effective native schema without importing application Python."""
import json
import os
from pathlib import Path
import shutil
import subprocess


def effective_schema_sql(root):
    explicit = os.environ.get('LOCALBRAIN_SCHEMA_EXECUTABLE')
    if explicit:
        executable = Path(explicit)
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError('LOCALBRAIN_SCHEMA_EXECUTABLE must name an existing absolute native binary')
        command = [str(executable), '--schema-ddl']
    else:
        cargo = shutil.which('cargo') or str(Path.home() / '.cargo/bin/cargo')
        command = [cargo, 'run', '--locked', '--quiet', '-p', 'localbrain-api', '--bin', 'localbrain', '--', '--schema-ddl']
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True)
    statements = json.loads(result.stdout)
    if not isinstance(statements, list) or not all(isinstance(statement, str) for statement in statements):
        raise ValueError('Invalid native schema response')
    return statements
