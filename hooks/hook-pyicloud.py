"""
PyInstaller hook for pyicloud library.
This ensures that all pyicloud services and dependencies are included in the build.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules from pyicloud
hiddenimports = collect_submodules('pyicloud')

# Collect any data files from pyicloud
datas = collect_data_files('pyicloud')

# Add specific pyicloud modules that might be missed
hiddenimports.extend([
    'pyicloud.services.photos',
    'pyicloud.services.drive',
    'pyicloud.services.calendar',
    'pyicloud.services.contacts',
    'pyicloud.services.reminders',
    'pyicloud.services.notes',
    'pyicloud.services.mail',
    'pyicloud.services.findmyiphone',
    'pyicloud.services.ubiquity',
    'pyicloud.services.account',
    'pyicloud.base',
    'pyicloud.exceptions',
    'pyicloud.utils',
    'pyicloud.version',
])
