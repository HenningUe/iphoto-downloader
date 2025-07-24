# 📄 Software Specification — iCloud Photo Sync Tool

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
     example "LOCALUSERDATA" on Windows systems) for a file named “settings.ini”
     inside a subfolder named "foto_pool".
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
   - The main entry-point function shall have a global try-except blocks
     handling flattly the whole function code block and send a pushover
     notification whenever a unhandled exception occurs
2. **2FA authenticaion**

2.1. Separate package 2FA authentication

- 2FA authentication shall be handled as a separate package
- The separate 2FA authentication package shall be placed in folder
  shared/auth2fa
- This package shall have its own test-suite, its own pyproject.toml, thus its
  own dependency list
- This package shall not depend on any code of the main icloud_photo_sync app

2.5. 2FA Trigger and Notification

- If 2FA authentication is required, the user shall be notified immediately via
  a Pushover notification.

2.6. Notification Content

- The Pushover notification shall include an HTTP link to a local address (e.g.,
  `http://<local-ip-address-of-pc>:<port>`), which directs the user to the local
  web interface.

2.7. Local Webserver

- A local webserver shall be started automatically when a 2FA authentication is
  required.

2.8. 2FA Session Handling

- The user shall be able to enter the 2FA key directly in the web interface
  provided by the local webserver.
- The webserver shall provide an interface that enables the user to trigger a
  new 2FA request via a button.

2.9. Folder structure

- All files related to the authentication topic shall be placed inside a python
  sub-package

2.10. HTTP Site Security

- The HTTP site does not need to be secured (i.e., no HTTPS), as the server runs
  only on the local machine within a private network.
- The server shall bind only to `<local-ip-address-of-pc>` or prevent external
  access.

2.11. Session Storage

- Each 2FA session shall be stored locally in the system’s default user
  directory (e.g., `%USERPROFILE%` on Windows or `$HOME` on Linux/macOS).
- The session data shall be stored in a dedicated sub-directory with an
  appropriate name (e.g., `2FA_Sessions`).
- Stored session data shall include only necessary information and follow
  security best practices (e.g., appropriate file permissions).

2.12. Error handling

- The system shall handle errors gracefully if the local server cannot start
  (e.g., due to the port being in use).

2.13. Logging

- 2FA requests and sessions may be logged for debugging or audit purposes. Logs
  shall not include sensitive user information.

3. **Local Deletion Tracking**
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
     "%LOCALAPPDATA%/foto_pool/deletion_tracker"
   - The environment variable "%LOCALAPPDATA%" shall be usable in windows and
     linux environments. In linux environments, this shall be replaced by a
     appropriate directory path, where user settings are stored on linux
     systems.

4. **Idempotent Runs**
   - Running the tool multiple times must not create duplicate files or
     unintended deletions.

---

### 2️⃣ Non-Functional Requirements

5. **Programming Language**
   - Python.

6. **iCloud API Integration**
   - Use the `pyicloud` package:
     [https://pypi.org/project/pyicloud/](https://pypi.org/project/pyicloud/)

7. **Package Management**
   - Use `uv` for managing dependencies:
     [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
   - Maintain all dependencies in `pyproject.toml`.

8. **Repository Structure**
   - Mono-repo structure as per the guide:
     [https://github.com/JasperHG90/uv-monorepo](https://github.com/JasperHG90/uv-monorepo)

9. **Version Control**
   - Git repository, hosted on GitHub.

10. **Executable Packaging**

- Build a standalone Windows .exe and a Linux executable using PyInstaller.
- The Linux build must be statically linked if possible, or provide clear
  runtime requirements.

11. **CI/CD Pipeline**

- Use GitHub Actions for building, testing, packaging, and releasing the
  executables for both Windows and Linux.
- Follow this guide for PyInstaller CI/CD:
  [https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)

---

### 3️⃣ Optional but Recommended

- Configurable local sync directory & secure credentials.
- Detailed logging to console & file.
- Dry-run mode for testing sync logic.
- Cross-platform support for running directly with Python.
- Clear user documentation.

---

## ✅ 4️⃣ Testing Requirements

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

## ✅ 5️⃣ Deliverables

- 📁 Mono-repo hosted on GitHub.
- ✅ `pyproject.toml` with dependencies.
- ✅ PyInstaller spec for building `.exe`.
- ✅ Automated GitHub Actions pipeline:
  - Install dependencies.
  - Run tests & linting.
  - Package Windows .exe and Linux executable.
  - The linux package shall be published as APT repository, see
    [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
  - The required APT-package-structure shall be taken into account, see
    [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
  - The windows package shall be published as WinGet package, see
    https://techwatching.dev/posts/wingetcreate
- ✅ Full unit & integration test suite.
- ✅ Example config or `.env` template.
- ✅ End-user documentation.

---

## ✅ 6️⃣ Acceptance Criteria

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
