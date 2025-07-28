"""
PyInstaller hook for fido2 library.
This ensures that the public_suffix_list.dat file is included in the build.
"""

from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from fido2 package
datas = collect_data_files('fido2')

# Ensure hidden imports for fido2 modules
hiddenimports = [
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
]
