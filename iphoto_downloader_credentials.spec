# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Credentials Manager Tool."""

import os
from pathlib import Path

# Define paths
src_path = Path('src/iphoto_downloader/src')
main_script = src_path / 'iphoto_downloader' / 'manage_credentials.py'

# Data files to include in the executable (minimal for credentials manager)
datas = []

# Include VERSION file for version display  
version_file = Path('VERSION')
if version_file.exists():
    datas.append(('VERSION', '.'))
    print(f"Added VERSION file to credentials manager: {version_file}")

# Include required files for delivery artifacts
user_guide = Path('USER-GUIDE.md')
if user_guide.exists():
    datas.append(('USER-GUIDE.md', '.'))

env_example = Path('.env.example')
if env_example.exists():
    datas.append(('.env.example', '.'))

block_cipher = None

a = Analysis(
    [str(main_script)],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Keyring backends for cross-platform credential storage
        'keyring.backends.Windows',
        'keyring.backends.macOS', 
        'keyring.backends.SecretService',
        'keyring.backends.kwallet',
        'keyring.backends.chainer',
        'keyring.backends.fail',
        # Core modules
        'iphoto_downloader',
        'iphoto_downloader.config',
        # Additional keyring dependencies
        'keyring',
        'keyring.util',
        'keyring.errors',
        # Platform-specific imports
        'win32api',
        'win32con',
        'win32cred',
        'pywintypes',
        # Fallback and utility modules
        'getpass',
        'sys',
        'os',
        're',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy dependencies not needed for credentials manager
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='iphoto_downloader_credentials',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='iphoto-downloader-credentials.png',
)
