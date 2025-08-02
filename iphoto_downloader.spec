# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for iCloud Photo Sync Tool."""

import os
from pathlib import Path

# Define paths
src_path = Path('src/iphoto_downloader/src')
main_script = src_path / 'iphoto_downloader' / 'main.py'

# Data files to include in the executable
datas = []

# Include repository files directly for delivery artifacts
repo_user_guide = Path('USER-GUIDE.md')
repo_env_example = Path('.env.example')
version_file = Path('VERSION')

if repo_user_guide.exists():
    datas.append((str(repo_user_guide), '.'))

if repo_env_example.exists():
    datas.append((str(repo_env_example), '.'))

# Include VERSION file for version display
if version_file.exists():
    datas.append((str(version_file), '.'))
    print(f"Added VERSION file: {version_file}")

# Include fido2 data files to fix missing public_suffix_list.dat error
try:
    import fido2
    import pkg_resources
    fido2_path = pkg_resources.resource_filename('fido2', 'public_suffix_list.dat')
    if os.path.exists(fido2_path):
        datas.append((fido2_path, 'fido2'))
        print(f"Added fido2 data file: {fido2_path}")
except (ImportError, Exception) as e:
    print(f"Warning: Could not locate fido2 data files: {e}")

# Alternative method to find fido2 data files
try:
    from PyInstaller.utils.hooks import collect_data_files
    fido2_datas = collect_data_files('fido2')
    if fido2_datas:
        datas.extend(fido2_datas)
        print(f"Added {len(fido2_datas)} fido2 data files via collect_data_files")
except Exception as e:
    print(f"Warning: collect_data_files for fido2 failed: {e}")

block_cipher = None

a = Analysis(
    [str(main_script)],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'keyring.backends.Windows',
        'keyring.backends.macOS',
        'keyring.backends.SecretService',
        'keyring.backends.kwallet',
        'iphoto_downloader',
        'iphoto_downloader.config',
        'iphoto_downloader.delivery_artifacts',
        'auth2fa',
        'auth2fa.pushover_service',
        # fido2 and related authentication modules
        'fido2',
        'fido2.rpid',
        'fido2.utils',
        'fido2.client',
        'fido2.server',
        'fido2.cbor',
        'fido2.cose',
        'fido2.ctap',
        'fido2.ctap1',
        'fido2.ctap2',
        'fido2.hid',
        'fido2.pcsc',
        'fido2.webauthn',
        # pyicloud dependencies
        'pyicloud',
        'pyicloud.services',
        'pyicloud.services.photos',
        'pyicloud.base',
        'pyicloud.exceptions',
        'pyicloud.utils',
        # Additional crypto and security modules
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.serialization',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='iphoto_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression to reduce false positives
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='iphoto-downloader-main.png',
    # Add version information to make executable appear more legitimate
    version='VERSION_INFO.txt',
)
