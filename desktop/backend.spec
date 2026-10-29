# Build from a clean Python 3.11 environment with the local-models extra installed.
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

project = Path(SPECPATH).parent
sys.path.insert(0, str(project / 'desktop'))
from build_support import write_sysconfig_hook

portable_hooks = write_sysconfig_hook(workpath)
metadata = []
for distribution in ('torch', 'transformers', 'huggingface-hub', 'sentence-transformers', 'tokenizers', 'safetensors', 'numpy', 'scikit-learn', 'tqdm', 'regex', 'requests', 'packaging', 'filelock', 'pyyaml', 'truststore'):
    metadata += copy_metadata(distribution)
datas = collect_data_files('localbrain', excludes=['**/google-oauth-client.json']) + collect_data_files('latex2mathml') + metadata
# Google CLI stays installed on each user PC; no Client or credentials are bundled.

hidden = ['uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto',
          'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on', 'tokenizers',
          'transformers.models.qwen3.modeling_qwen3', 'transformers.models.qwen3.configuration_qwen3',
          'transformers.models.qwen2.tokenization_qwen2_fast', 'sentence_transformers']
hidden += collect_submodules('sentence_transformers')
a = Analysis([str(project / 'desktop' / 'backend-entry.py')], pathex=[str(project / 'src')],
             binaries=[], datas=datas, hiddenimports=hidden,
             hookspath=[portable_hooks],
             excludes=['tkinter', 'matplotlib', 'IPython', 'pytest', 'tensorboard', 'tensorflow', 'keras', 'jax'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='localbrain-backend', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=True, target_arch='arm64',
          codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='localbrain-backend')
