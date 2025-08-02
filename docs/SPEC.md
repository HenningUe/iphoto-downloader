# 📄 Software Specification — iPhoto Downloader Tool

## Overview

The goal is to develop a **Python-based tool** that synchronizes photos from an
iCloud account to a local directory. It must **only download new photos** and
must respect local deletions — i.e., if a photo is deleted locally, it must not
be re-synced. The tool **must not delete any photos** from the iCloud account.

The project will be managed as a **mono-repo** using **uv** for dependency
management, hosted on **GitHub**, and packaged into a standalone **Windows
`.exe`** using **PyInstaller**. CI/CD will build and release the executable
automatically using **GitHub Actions**.

---

## ✅ Requirements

### 1️⃣ Functional Requirements

1. **Photo Sync**
   - Sync photos from iCloud to a local directory.
   - Settings shall be provided via an .env file inside repository
   - If the local ".env" file is not available in the current directory and the
     app shall search in the respective system user settings directory (for
     example "LOCALUSERDATA" on Windows systems) for a file named "settings.ini"
     inside a subfolder named "iphoto_downloader".
   - There shall be a parallel .env-file named .env.example which works as
     template. This shall not contain any secrets.
   - It shall be possible to specify whether personal i-cloud-albums shall be
     included at all. Parameter of type bool shall be 'include_personal_albums'
   - It shall be possible to specify which personal albums shall be included via
     an allow-list. If the allow-list is empty all are included. As the
     allow-list is defined in the .env file the list-items shall be comma
     separated. Parameter of shall be 'personal_album_names_to_include'
   - It shall be possible to specify whether shared albums shall be included at
     all. Parameter of type bool shall be 'include_shared_albums'
   - It shall be possible to specify which shared albums shall be included via
     an allow-list. If the allow-list is empty all are included. As the
     allow-list is defined in the .env file the list-items shall be comma
     separated. Parameter of shall be 'shared_album_names_to_include'
   - For each album a separate folder shall be created underneath
     'SYNC_DIRECTORY'. Photos should be placed in the corresponding subfolder of
     their album.
   - These settings shall be provided by the used inside the settings-file (e.g.
     .env)
   - Only download photos that do not yet exist locally.
   - If a photo is deleted locally, it must **not** be re-downloaded on the next
     sync.
   - Locally deleted photos must **not** be removed from iCloud.
   - To track the fotos (to avoid duplicated downloads) a sqlite data-base shall
     be used
   - The fotos in this database shall be identifed by their name and their
     source album-name
   - shall run on windows and linux
   - credentials (iCloud and pushover) shall be storable via keyrind
   - if credentials are not yet stored on local PC at startup of the App they
     should be request via input (CLI)
   - credentials shall be stored for icloud and for pushover
   - A separate app shall be provided, which allows credential management. That
     means user must be able to store, delete and check credentials

2. **Operation modes**
   - The app shall be either executed in single execution mode (i.e. start
     synchronization and stop after synchronization run is completed) or run
     continuously.
   - If the app runs continuously it shall wait 2 minutes after the completion
     if the lass successfully completed synchronization run and before the
     execution of the next synchronization run.
   - If the app runs continuously the database integrity check and creation of
     backups shall be done every hour (see chapter **Local Deletion Tracking**)
   - If the database integrity check and backup is done, the synchronisation
     shall be paused to avoid any conflicts.
   - The app execution mode (single or continuous) shall be defined in the
     settings file. If nothing is provided the default shall be single
     execution.

   - The app shall run allow multiple instances or run as single instance only.
   - If only one instance is allowed, a message shall be printed, that another
     instance is already running and abort immediately
   - It shall be configurable in the settings if multi-instances are allowed.
     The related settings key shall be "allow_multi_instance". The default value
     shall be false.

3. **Global exception handling**
   - The main entry-point function shall have a global try-except blocks
     handling flattly the whole function code block and send a pushover
     notification whenever a unhandled exception occurs

4. **Consideration of delivery artifacts**
   - It should be possible to define two operating modes in the settings:
     "InDevelopment" and "Delivered" - When the "Delivered" operating mode is
     activated, the system should check whether the settings folder (see section
     **Photo Sync**) exists and whether the files USER-GUIDE.md,
     settings.ini.template, and settings.ini are located there. If any of these
     files are missing, they should be copied there and the program should be
     terminated. In addition, the user should be informed that the files have
     been copied and where exactly, what the files are for, and that they should
     run this program again after adjusting settings.ini.
   - If the files are present, the program should perform its normal function.
   - In "Delivered" mode, READMD.md and settings.ini.template should be copied
     to the settings folder each time the program is started (but not
     settings.ini).
   - READMD.md and .env.example (as source for settings.ini.template ) from the
     repository are to be used. I.e. when the executable is created these files
     must be included in the executable as additional resources. The content of
     the created READM.md and shall **not** be included in a python file as
     strings to avoid duplicated sources.
   - The default mode for operation in development environment shall be
     "InDevelopment"

5. **2FA authenticaion**

5.1. Separate package 2FA authentication

- 2FA authentication shall be handled as a separate package
- The separate 2FA authentication package shall be placed in folder
  shared/auth2fa
- This package shall have its own test-suite, its own pyproject.toml, thus its
  own dependency list
- This package shall not depend on any code of the main iphoto_downloader app

5.2. 2FA Trigger and Notification

- If 2FA authentication is required, the user shall be notified immediately via
  a Pushover notification.

5.3. Notification Content

- The Pushover notification shall include an HTTP link to a local address (e.g.,
  `http://<local-ip-address-of-pc>:<port>`), which directs the user to the local
  web interface.

5.4. Local Webserver

- A local webserver shall be started automatically when a 2FA authentication is
  required.

5.5. 2FA Session Handling

- The user shall be able to enter the 2FA key directly in the web interface
  provided by the local webserver.
- The webserver shall provide an interface that enables the user to trigger a
  new 2FA request via a button.

5.6. Folder structure

- All files related to the authentication topic shall be placed inside a python
  sub-package

5.7. HTTP Site Security

- The HTTP site does not need to be secured (i.e., no HTTPS), as the server runs
  only on the local machine within a private network.
- The server shall bind only to `<local-ip-address-of-pc>` or prevent external
  access.

5.8. Session Storage

- Each 2FA session shall be stored locally in the system’s default user
  directory (e.g., `%USERPROFILE%` on Windows or `$HOME` on Linux/macOS).
- The session data shall be stored in a dedicated sub-directory with an
  appropriate name (e.g., `2FA_Sessions`).
- Stored session data shall include only necessary information and follow
  security best practices (e.g., appropriate file permissions).

5.9. Error handling

- The system shall handle errors gracefully if the local server cannot start
  (e.g., due to the port being in use).

5.10. Logging

- 2FA requests and sessions may be logged for debugging or audit purposes. Logs
  shall not include sensitive user information.

6. **Local Deletion Tracking**
   - Persistently track which files have been deleted locally to avoid
     re-downloading.
   - Use a local lightweight database (e.g., SQLite or a JSON file) for
     tracking.
   - A backup-copy of the local database shall be maintained. Before the start
     of a synchronization run, the backup copy shall be created
   - If the database is corrupted, i.e. can not be opened anymore, it shall be
     restored from the backup-copy.
   - If the local database is not available, but a backup-copy it shall be
     restored from the backup-copy.
   - If the local database and the backup-copy are not availabe a new database
     shall be created.
   - The database's parent directory location shall be specifiable in the
     settings-file. It shall be possible to provide relative and absolute path.
     If a relative path is provided it shall refer to the folder to which the
     photos are downloaded
   - The database's default value shall be ".data", i.e. inside the photos
     folder, e.g. "test_photos/.data".
   - It shall be possible to provide environment-variables, e.g.
     "%LOCALAPPDATA%/iphoto_downloader/deletion_tracker"
   - The environment variable "%LOCALAPPDATA%" shall be usable in windows and
     linux environments. In linux environments, this shall be replaced by a
     appropriate directory path, where user settings are stored on linux
     systems.

7. **Idempotent Runs**
   - Running the tool multiple times must not create duplicate files or
     unintended deletions.

8. **Versioning**
   - Versioning shall be semver based
   - When a new release is created, a plain text file named "VERSION" which
     stores the release version as text shall be created. This file shall be
     included as artefact in the executable created by PyInstaller. The version
     stored in this VERSION file shall be included in the start-up message, when
     the app is started. This is true for both apps, iphoto_downloader and
     iphoto_downloader_credentials. In development environment (i.e. the VERSION
     file does not exist), the release shall be simply "dev". This shall be
     included in the code and the ci-pipelines (see chapter below **CI/CD
     Pipeline**)

---

### 2️⃣ Non-Functional Requirements

1. **Programming Language**
   - Python.

2. **iCloud API Integration**
   - Use the `pyicloud` package:
     [https://pypi.org/project/pyicloud/](https://pypi.org/project/pyicloud/)

3. **Package Management**
   - Use `uv` for managing dependencies:
     [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
   - Maintain all dependencies in `pyproject.toml`.

4. **Repository Structure**
   - Mono-repo structure as per the guide:
     [https://github.com/JasperHG90/uv-monorepo](https://github.com/JasperHG90/uv-monorepo)

5. **Version Control**
   - Git repository, hosted on GitHub.

6. **Executable Packaging**

6.1. **Main Executable Packaging**

- Build a standalone (single file) Windows .exe and a Linux executable using
  PyInstaller for the main executable, which is based on #main.py as first entry
  point.
- The app shall have the image #iphoto-downloader-main.png as App icon
- When the executable is used the modus "Delivered" (decribed in chapter
  **Consideration of delivery artifacts**) shall be the default one.
- Both files "READMD.md" and ".env.example" must be included in the executable
  as additional resources to be available later on for copying, see chapter
  **Consideration of delivery artifacts**
- The Linux build must be statically linked if possible, or provide clear
  runtime requirements.

6.2. **Credentials Manager Executable Packaging**

- Build a standalone (single file) Windows .exe and a Linux executable using
  PyInstaller for the iphoto_downloader_credentials executable, which is based
  on #manage_credentials.py as first entry point.
- The app shall have the image #iphoto-downloader-credentials.png as App icon
- The Linux build must be statically linked if possible, or provide clear
  runtime requirements.

7. **CI/CD Pipeline**

- Use GitHub Actions for building, testing, packaging, and releasing the
  executables for both Windows and Linux.
- Follow this guide for PyInstaller CI/CD
  [https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)
- The previously given link shall be used considering the following adpations:
  - the release workflow shall be trigger, whenever a new release is requested
    in github for this repo, i.e. link "https://github.com/.../releases/new" is
    called
  - The release workflow shall created executables for windows and linux
  - Before the creation of the executables the test-suite shall be executed. Any
    error shall cause an aboration. The tests which are included, shall not be
    blocked by any required user-interaction.
  - The windows executable shall be published automatically to winget, i.e. the
    Windows Package Manager.
  - The linux executable shall be published automatically to APT (Advanced
    Packaging Tool), i.e. the ubuntu package manager
  - The release in the github.downloads section should contain two ZIP files, one for Windows and one for Linux (Ubuntu). Each ZIP file should contain the respective executables “iphoto_downloader” and “iphoto_downloader_credentials.” In addition, the source code should be available as a ZIP file in the download section. No other files should be included. The zip files should include the version name as a suffix.
  - The executables should not trigger a virus alert, e.g. Mircosoft Defender or similar tools.
  - The executable shall be submitted to virustotal (https://www.virustotal.com/gui/home/upload) as false-positive
  - The executable shall be submitted to microsoft antivirus (https://www.microsoft.com/en-us/wdsi/filesubmission) as false-positive

---

### 3️⃣ Optional but Recommended

- Configurable local sync directory & secure credentials.
- Detailed logging to console & file.
- Dry-run mode for testing sync logic.
- Cross-platform support for running directly with Python.
- Clear user documentation.

---

## ✅ 5️⃣ Testing Requirements

**Purpose:** Ensure high reliability, protect iCloud data integrity, and verify
that local deletion tracking works as specified.

**Scope of Testing:**

1. **Unit Tests**
   - Core sync logic:
     - Identify new photos.
     - Correctly skip already downloaded photos.
     - Correctly skip locally deleted photos.
   - Local deletion tracking logic.
   - Database or file persistence for deleted photo tracking.
   - Utility functions (e.g., file system operations).

2. **Integration Tests**
   - Mocked iCloud interaction:
     - Verify that the tool interacts correctly with the `pyicloud` API.
     - Simulate partial downloads, API errors, and retries.
   - Test local sync end-to-end with dummy files and directories.

3. **End-to-End Tests** _(Optional but recommended)_
   - Run the tool in a test mode against a dummy or sandboxed iCloud account (or
     fully mocked).
   - Verify that:
     - New photos are downloaded.
     - Local deletions are respected.
     - No unintended deletions occur on iCloud.

4. **Test Automation**
   - Tests must run automatically in the CI/CD pipeline on each pull request and
     push.
   - Minimum coverage target (recommended: 80%+ for core sync logic).
   - Linting and static checks using `ruff` and `mypy`

5. **Manual Tests**
   - Run the `.exe` on Windows to verify:
     - The packaged app starts successfully.
     - It syncs as expected.
     - No credentials are accidentally embedded in the binary.
     - The app handles credential failures gracefully.

---

## ✅ 6️⃣ Deliverables

- 📁 Mono-repo hosted on GitHub.
- ✅ `pyproject.toml` with dependencies.
- ✅ PyInstaller spec for building `.exe`.
- ✅ Automated GitHub Actions pipeline:
  - Install dependencies.
  - Run tests & linting.
  - Package Windows .exe and Linux executable.
  - The linux package shall be published as snap package, see
    [https://www.digitalocean.com/community/tutorials/how-to-package-and-publish-a-snap-application-on-ubuntu-18-04](https://www.digitalocean.com/community/tutorials/how-to-package-and-publish-a-snap-application-on-ubuntu-18-04)
  - The required snap-package-structure shall be taken into account, see
    [https://www.digitalocean.com/community/tutorials/how-to-package-and-publish-a-snap-application-on-ubuntu-18-04](https://www.digitalocean.com/community/tutorials/how-to-package-and-publish-a-snap-application-on-ubuntu-18-04)
  - The windows package shall be published as WinGet package, see
    https://techwatching.dev/posts/wingetcreate
- ✅ Full unit & integration test suite.
- ✅ Example config or `.env` template.
- ✅ End-user documentation.

---

## ✅ 7️⃣ Acceptance Criteria

- ✔️ No re-download of locally deleted photos.
- ✔️ No accidental deletions from iCloud.
- ✔️ Tool runs idempotently.
- ✔️ `.exe` builds automatically and runs on Windows.
- ✔️ All tests pass in CI/CD.
- ✔️ Clear logs for sync operations.
- ✔️ Versioned releases on GitHub.

---

## ✅ References

- **pyicloud**:
  [https://pypi.org/project/pyicloud/](https://pypi.org/project/pyicloud/)
- **uv**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- **uv Monorepo Guide**:
  [https://github.com/JasperHG90/uv-monorepo](https://github.com/JasperHG90/uv-monorepo)
- **PyInstaller CI/CD Guide**:
  [https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)
- **APT Repository**:
  [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)

---

**End of Specification**
