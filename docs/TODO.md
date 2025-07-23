This is the project TODO list for implementing the **iCloud Photo Sync Tool** as
specified.

---

## 1️⃣ 📁 Project Setup

- [x] Create **GitHub repo** with mono-repo structure
      ([uv monorepo guide](https://github.com/JasperHG90/uv-monorepo))
- [x] Initialize **`pyproject.toml`** using `uv`
- [x] Add `pyicloud` dependency
- [x] Add linting tools: `ruff`, `mypy`
- [x] Add `.gitignore` for Python, build outputs, and virtual environments
- [x] Add `README.md` with project overview

---

## 2️⃣ ⚙️ Core Logic

### 2.1 Core Sync Logic

- [x] Implement **iCloud authentication** using `pyicloud`
- [x] Implement **configurable local sync directory**
- [x] Develop logic to:
  - [x] List all photos in iCloud
  - [x] Identify which photos already exist locally
  - [x] Check local deletion database for deleted photos
  - [x] Download only new photos
  - [ ] Download of albums shall be possible.
  - [ ] Photos should be placed in the corresponding subfolder of their album.
- [x] Ensure **idempotent runs** (no duplicates)
- [x] Add **dry-run mode** to show sync actions without modifying files

#### 2.1.1 Album Filtering & Selection

- [ ] Implement **personal album filtering**:
  - [ ] Add `include_personal_albums` boolean configuration parameter
  - [ ] Add `personal_album_names_to_include` comma-separated list parameter in
        .env
  - [ ] Based `personal_album_names_to_include` in .env a equally named variable
        shall be used inside the python code, which takes the value from .env
        and splits this into single string items, putting them into an list
  - [ ] Implement logic to skip personal albums if
        `include_personal_albums=false`
  - [ ] Implement allow-list filtering for personal albums (empty list = include
        all)
  - [ ] If `personal_album_names_to_include` is filled, a check shall be
        included, which breaks, if the any of the specified albumes does not
        exist
- [ ] Implement **shared album filtering**:
  - [ ] Add `include_shared_albums` boolean configuration parameter
  - [ ] Add `shared_album_names_to_include` comma-separated list parameter
  - [ ] Based `shared_album_names_to_include` in .env a equally named variable
        shall be used inside the python code, which takes the value from .env
        and splits this into single string items, putting them into an list
  - [ ] Implement logic to access shared albums via pyicloud API
  - [ ] Implement allow-list filtering for shared albums (empty list = include
        all)
  - [ ] If `shared_album_names_to_include` is filled, a check shall be included,
        which breaks, if the any of the specified albumes does not exist
- [ ] Enhance **photo enumeration** to support album-based filtering:
  - [ ] Modify photo listing to iterate through selected albums only
  - [ ] Ensure photos from multiple albums are not duplicated
  - [ ] Handle photos that exist in multiple selected albums

#### 2.1.2 Enhanced Photo Tracking

- [ ] Upgrade **SQLite database schema** for album-aware tracking:
  - [ ] Add `source_album_name` column to photos table
  - [ ] Create composite primary key using (photo_name, source_album_name)
  - [ ] Add database migration logic for existing installations
- [ ] Implement **album-aware photo identification**:
  - [ ] Track photos by combination of filename and source album
  - [ ] Handle same photo existing in multiple albums
  - [ ] Update deletion tracking to include album context
- [ ] Update **sync logic** for album-based tracking:
  - [ ] Check database using (photo_name, album_name) combination
  - [ ] Record downloads with source album information
  - [ ] Ensure deletion tracking works per album

### 2.2 2FA Authentication System

#### 2.2.1 📱 Pushover Notification Integration

- [x] Add `requests` dependency to `pyproject.toml` (for Pushover API)
- [x] Implement **Pushover notification service** for 2FA triggers
- [x] Create configuration for Pushover API token & user key
- [x] Implement notification content with HTTP link to local webserver
- [x] Add error handling for Pushover API failures

#### 2.2.2 🌐 Local Web Server

- [x] Implement **local HTTP server** (Flask/FastAPI) for 2FA interface
- [x] Create web interface with:
  - [x] Button to trigger new 2FA request
  - [x] Input field for 2FA code entry
  - [x] Status display for authentication progress
- [x] Ensure server binds only to `localhost`/`127.0.0.1`
- [x] Implement **automatic server startup** when 2FA required
- [x] Add **port conflict handling** (try multiple ports if needed)

#### 2.2.3 🔄 2FA Session Management

- [x] Implement **2FA session initiation** via web interface
- [x] Add **2FA code validation** through web form
- [x] Integrate with existing `pyicloud` 2FA handling
- [x] Implement **session state management** (pending, authenticated, failed)

#### 2.2.4 💾 Session Storage

- [x] Store 2FA sessions in user directory (`%USERPROFILE%` or `$HOME`)
- [x] Create dedicated subdirectory (`icloud_photo_sync/sessions`)
- [x] Implement secure file permissions for session data
- [x] Store only necessary session information
- [x] Add **session cleanup** for expired sessions

#### 2.2.5 🛡️ Security & Error Handling

- [x] Implement **graceful error handling** for server startup failures
- [x] Add **port availability checking** before server start
- [x] Implement **session timeout** mechanisms
- [x] Add **rate limiting** for 2FA attempts
- [x] Ensure no sensitive data in logs

#### 2.2.6 📝 2FA Logging

- [x] Add **2FA-specific logging** for debugging
- [x] Log 2FA requests and session states (without sensitive data)
- [x] Implement **audit trail** for 2FA sessions
- [x] Add **structured logging** for 2FA events

### 2.3 Local Deletion Tracking

- [x] Design lightweight **SQLite** or **JSON-based** local deletion tracker
- [x] Create functions to:
  - [x] Record deleted files when missing locally
  - [x] Persistently update tracker on each sync
- [x] Integrate deletion tracker with sync logic

#### 2.3.1 Album-Aware Deletion Tracking

- [ ] Enhance **deletion tracking schema**:
  - [ ] Update database to track deletions by (photo_name, source_album_name)
  - [ ] Add migration for existing deletion records
  - [ ] Ensure deletion tracking works independently per album
- [ ] Update **deletion detection logic**:
  - [ ] Check for locally deleted photos per album context
  - [ ] Handle cases where same photo exists in multiple albums
  - [ ] Prevent re-download of photos deleted from specific albums

---

## 5️⃣ 🧪 Tests

- [x] Write **unit tests** for:
  - [x] Photo listing & new photo detection
  - [x] Local deletion tracking logic
  - [x] Database read/write functions
  - [x] File system utilities
- [x] Write **integration tests** with mocked `pyicloud`:
  - [x] Simulate new photos, already downloaded photos, deleted photos
  - [x] Simulate API errors & retry logic
- [ ] Add **2FA system tests**:
  - [ ] Test Pushover notification sending
  - [ ] Test local web server startup/shutdown
  - [ ] Test 2FA code validation via web interface
  - [ ] Test session storage and retrieval
  - [ ] Test error handling (port conflicts, API failures)
- [ ] Add **album filtering tests**:
  - [ ] Test personal album include/exclude logic
  - [ ] Test shared album include/exclude logic
  - [ ] Test album allow-list filtering (empty list = all albums)
  - [ ] Test comma-separated album name parsing
  - [ ] Test album-aware photo enumeration
- [ ] Add **enhanced tracking tests**:
  - [ ] Test album-aware photo identification
  - [ ] Test (photo_name, album_name) composite tracking
  - [ ] Test album-aware deletion tracking
  - [ ] Test database migration for album-aware schema
  - [ ] Test handling of photos in multiple albums
- [ ] (Optional) Add **end-to-end test** using dummy or sandbox iCloud
- [ ] Add all tests to CI/CD
- [x] Achieve ≥ **80% test coverage** for core sync logic (✅ **85.21%**
      achieved)

---

## 6️⃣ 🐧🪟 Cross-Platform Build

- [ ] Write **PyInstaller spec** for Windows `.exe`
- [ ] Write **PyInstaller spec** for Linux executable (consider static linking
      if possible)
- [ ] Test builds locally on Windows and Linux
- [ ] Ensure **2FA web server** works in packaged builds
- [ ] Test **Pushover notifications** in packaged builds

---

## 7️⃣ 🔁 CI/CD Pipeline (GitHub Actions)

- [ ] Create **CI workflow**:
  - [ ] Install dependencies using `uv`
  - [ ] Run unit & integration tests
  - [ ] Run `ruff` and `mypy`
  - [ ] Build `.exe` for Windows and executable for Linux
  - [ ] Package Linux build for **APT repo**
        ([APT guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository))
  - [ ] Package Windows build for **WinGet**
        ([WinGetCreate](https://techwatching.dev/posts/wingetcreate))
  - [ ] Publish releases automatically

---

## 8️⃣ 🧩 Configuration & Security

- [x] Add example `.env` template for credentials
- [x] Support configurable local sync directory
- [x] Add **Pushover configuration** (API token, user key)
- [ ] Add **2FA web server configuration** (port range, bind address)
- [ ] Add **album filtering configuration**:
  - [ ] Add `include_personal_albums` boolean parameter to .env template
  - [ ] Add `personal_album_names_to_include` comma-separated list parameter
  - [ ] Add `include_shared_albums` boolean parameter to .env template
  - [ ] Add `shared_album_names_to_include` comma-separated list parameter
  - [ ] Update .env.example with album filtering examples
  - [ ] Add configuration validation for album parameters
- [ ] Ensure credentials are not bundled in builds
- [x] Implement robust **logging** to console & file

---

## 9️⃣ 📜 Documentation

- [ ] Write **user guide**:
  - [ ] How to install (Windows & Linux)
  - [ ] How to configure sync dir & credentials
  - [ ] How to configure **Pushover notifications**
  - [ ] How **2FA web interface** works
  - [ ] How to run dry-run mode
  - [ ] How local deletion tracking works
  - [ ] **2FA troubleshooting guide**
  - [ ] **Album filtering configuration guide**:
    - [ ] How to configure personal album filtering
    - [ ] How to configure shared album filtering
    - [ ] How to use album allow-lists
    - [ ] Examples of album filtering configurations
    - [ ] How album-aware tracking works
- [ ] Include usage examples & troubleshooting tips

---

## 1️⃣0️⃣ ✅ Manual Verification

- [ ] Test `.exe` on Windows:
  - [ ] App runs and syncs as expected
  - [ ] **2FA web server** starts correctly
  - [ ] **Pushover notifications** are sent
  - [ ] **2FA web interface** works properly
  - [ ] **Album filtering** works correctly (personal & shared)
  - [ ] **Album allow-lists** are respected
  - [ ] **Album-aware tracking** prevents duplicates correctly
  - [ ] No credentials leaked in binary
  - [ ] Handles credential failures gracefully
- [ ] Test Linux executable:
  - [ ] All 2FA features work on Linux
  - [ ] All album filtering features work on Linux
  - [ ] Cross-platform session storage works
  - [ ] Cross-platform album-aware database works

---

## 1️⃣1️⃣ 🚀 Release

- [ ] Tag a versioned release on GitHub
- [ ] Verify Linux package published to **APT repo**
- [ ] Verify Windows build published to **WinGet**
- [ ] Test install & run on fresh Windows/Linux machine
- [ ] Verify **2FA system** works on fresh installations

---

## 🎉 DONE when:

- ✔️ No re-downloads of locally deleted photos
- ✔️ No accidental deletions on iCloud
- ✔️ Idempotent sync runs
- ✔️ **Personal album filtering** works (include/exclude, allow-lists)
- ✔️ **Shared album filtering** works (include/exclude, allow-lists)
- ✔️ **Album-aware photo tracking** prevents duplicates across albums
- ✔️ **Enhanced database schema** tracks photos by (name, album) composite key
- ✔️ **2FA notifications via Pushover work**
- ✔️ **Local web server for 2FA works**
- ✔️ **2FA sessions are stored securely**
- ✔️ `.exe` builds automatically and runs on Windows
- ✔️ CI/CD builds, tests, packages, and releases
- ✔️ Clear logs for all sync operations
- ✔️ Versioned releases available to users
- ✔️ Users can easily install & configure
- ✔️ **Album filtering configuration** is well documented

---

**References:**

- [pyicloud](https://pypi.org/project/pyicloud/)
- [uv](https://docs.astral.sh/uv/)
- [uv Monorepo Guide](https://github.com/JasperHG90/uv-monorepo)
- [PyInstaller CI/CD Guide](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)
- [APT Repo Guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
- [WinGetCreate](https://techwatching.dev/posts/wingetcreate)

---
