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
  - [x] Download of albums shall be possible.
  - [x] Photos should be placed in the corresponding subfolder of their album.
- [x] Ensure **idempotent runs** (no duplicates)
- [x] Add **dry-run mode** to show sync actions without modifying files

#### 2.1.1 Album Filtering & Selection

- [x] Implement **personal album filtering**:
  - [x] Add `include_personal_albums` boolean configuration parameter
  - [x] Add `personal_album_names_to_include` comma-separated list parameter in
        .env
  - [x] Based `personal_album_names_to_include` in .env a equally named variable
        shall be used inside the python code, which takes the value from .env
        and splits this into single string items, putting them into an list
  - [x] Implement logic to skip personal albums if
        `include_personal_albums=false`
  - [x] Implement allow-list filtering for personal albums (empty list = include
        all)
  - [x] If `personal_album_names_to_include` is filled, a check shall be
        included, which breaks, if the any of the specified albumes does not
        exist
- [x] Implement **shared album filtering**:
  - [x] Add `include_shared_albums` boolean configuration parameter
  - [x] Add `shared_album_names_to_include` comma-separated list parameter
  - [x] Based `shared_album_names_to_include` in .env a equally named variable
        shall be used inside the python code, which takes the value from .env
        and splits this into single string items, putting them into an list
  - [x] Implement logic to access shared albums via pyicloud API
  - [x] Implement allow-list filtering for shared albums (empty list = include
        all)
  - [x] If `shared_album_names_to_include` is filled, a check shall be included,
        which breaks, if the any of the specified albumes does not exist
- [x] Enhance **photo enumeration** to support album-based filtering:
  - [x] Modify photo listing to iterate through selected albums only
  - [x] Ensure photos from multiple albums are not duplicated
  - [x] Handle photos that exist in multiple selected albums

#### 2.1.2 Enhanced Photo Tracking

- [x] Upgrade **SQLite database schema** for album-aware tracking:
  - [x] Add `source_album_name` column to photos table
  - [x] Create composite primary key using (photo_name, source_album_name)
  - [x] Add database migration logic for existing installations
- [x] Implement **album-aware photo identification**:
  - [x] Track photos by combination of filename and source album
  - [x] Handle same photo existing in multiple albums
  - [x] Update deletion tracking to include album context
- [x] Update **sync logic** for album-based tracking:
  - [x] Check database using (photo_name, album_name) combination
  - [x] Record downloads with source album information
  - [x] Ensure deletion tracking works per album

#### 2.1.3 Continuous Execution Mode

- [x] Implement **execution mode configuration**:
  - [x] Add `execution_mode` parameter to settings file (single/continuous)
  - [x] Set default execution mode to "single" if not specified
  - [x] Add configuration validation for execution mode parameter
- [x] Implement **single execution mode**:
  - [x] Start synchronization and stop after completion
  - [x] Ensure proper cleanup and resource release after sync
- [x] Implement **continuous execution mode**:
  - [x] Run synchronization in a loop with controlled intervals
  - [x] Wait 2 minutes after successful sync completion before next run
  - [x] Handle graceful shutdown on interruption (Ctrl+C, SIGTERM)
- [x] Implement **hourly database maintenance** in continuous mode:
  - [x] Perform database integrity check every hour
  - [x] Create database backups every hour (see chapter Local Deletion Tracking)
  - [x] Schedule maintenance independently from sync cycles
  - [x] Log all maintenance activities
  - [x] Pause synchronization during database integrity check and backup to
        avoid conflicts

#### 2.1.4 Delivery Artifacts Management

- [x] Implement **operating mode detection**:
  - [x] Add configuration parameter for operating mode ("InDevelopment"/"Delivered")
  - [x] Implement mode validation and default value assignment
  - [x] Add mode-specific behavior switching in main application logic
- [x] Implement **"Delivered" mode functionality**:
  - [x] Add settings folder path detection based on user directory structure
  - [x] Implement required files existence check (README.md, settings.ini.template, settings.ini)
  - [x] Create file copying mechanism for missing delivery artifacts
  - [x] Add user notification system for copied files with detailed location info
  - [x] Implement graceful program termination after file copying
- [x] Implement **automatic file management in "Delivered" mode**:
  - [x] Copy README.md to settings folder on every startup (overwrite existing)
  - [x] Copy .env.example to settings folder on every startup (overwrite existing). Change target file name depending on the context. I.e. either ".env" or "settings.ini".
  - [x] Preserve existing settings.ini file (never overwrite)
  - [x] Add file copy operation logging and error handling
- [x] Integrate **delivery mode with packaging**:
  - [x] Ensure PyInstaller executable defaults to "Delivered" mode
  - [x] Include required template files in executable build
  - [x] Test delivery artifacts deployment in packaged builds

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
- [x] Add **global exception handling** in main entry-point function:
  - [x] Implement global try-except block around main function
  - [x] Send Pushover notification for unhandled exceptions
  - [x] Include relevant error details in notification (without sensitive data)
  - [x] Ensure graceful application shutdown on critical errors

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

#### 2.3.1 Database Safety & Recovery

- [x] Implement **database safety copy mechanism**:
  - [x] Create safety copy of local database before each synchronization run
  - [x] Store safety copy in designated backup location
  - [x] Implement automatic backup rotation (keep recent backups)
- [x] Implement **database corruption detection**:
  - [x] Check database integrity at startup
  - [x] Detect when database cannot be opened
  - [x] Implement database corruption recovery logic
- [x] Implement **database recovery procedures**:
  - [x] Restore from safety copy when database is corrupted
  - [x] Restore from safety copy when local database is missing
  - [x] Create new database when both local and safety copy are unavailable
  - [x] Log all database recovery operations
- [x] Add **backup management**:
  - [x] Cleanup old safety copies to prevent disk space issues
  - [x] Verify safety copy integrity before using for recovery
  - [x] Add configuration for backup retention policy

#### 2.3.2 Album-Aware Deletion Tracking

- [x] Enhance **deletion tracking schema**:
  - [x] Update database to track deletions by (photo_name, source_album_name)
  - [x] Add migration for existing deletion records
  - [x] Ensure deletion tracking works independently per album
- [x] Update **deletion detection logic**:
  - [x] Check for locally deleted photos per album context
  - [x] Handle cases where same photo exists in multiple albums
  - [x] Prevent re-download of photos deleted from specific albums

#### 2.3.3 Database Path Configuration

- [x] Implement **configurable database location**:
  - [x] Add database parent directory setting in configuration file
  - [x] Support both relative and absolute paths
  - [x] Relative paths should be relative to photo download directory
  - [x] Set default database location to ".data" subfolder (e.g.,
        "test_photos/.data")
- [x] Add **environment variable support**:
  - [x] Support environment variables in database path configuration
  - [x] Implement cross-platform "%LOCALAPPDATA%" environment variable support
  - [x] Map "%LOCALAPPDATA%" to appropriate Linux user settings directory
  - [x] Add path expansion and validation for environment variables
- [x] Update **database initialization logic**:
  - [x] Modify DeletionTracker to accept configurable database path
  - [x] Ensure database directory creation with proper permissions
  - [x] Update backup and recovery mechanisms for configurable paths
  - [x] Add configuration validation for database path settings

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
- [x] Add **2FA system tests**:
  - [x] Test Pushover notification sending
  - [x] Test local web server startup/shutdown
  - [x] Test 2FA code validation via web interface
  - [x] Test session storage and retrieval
  - [x] Test error handling (port conflicts, API failures)
- [x] Add **album filtering tests**:
  - [x] Test personal album include/exclude logic
  - [x] Test shared album include/exclude logic
  - [x] Test album allow-list filtering (empty list = all albums)
  - [x] Test comma-separated album name parsing
  - [x] Test album-aware photo enumeration
- [x] Add **enhanced tracking tests**:
  - [x] Test album-aware photo identification
  - [x] Test (photo_name, album_name) composite tracking
  - [x] Test album-aware deletion tracking
  - [x] Test database migration for album-aware schema
  - [x] Test handling of photos in multiple albums
- [x] Add **database path configuration tests**:
  - [x] Test custom database path configuration
  - [x] Test environment variable expansion (%LOCALAPPDATA%, $HOME)
  - [x] Test relative vs absolute path handling
  - [x] Test cross-platform path compatibility
  - [x] Test database creation in custom paths
  - [x] Test error handling for invalid/inaccessible paths
- [x] Add **delivery artifacts tests**:
  - [x] Test operating mode detection and validation
  - [x] Test "InDevelopment" vs "Delivered" mode behavior
  - [x] Test settings folder detection across platforms
  - [x] Test required files existence checking
  - [x] Test file copying mechanism for missing artifacts
  - [x] Test user notification system for copied files
  - [x] Test graceful program termination after file operations
  - [x] Test automatic file updates in "Delivered" mode (README.md, settings.ini.template)
  - [x] Test settings.ini preservation in "Delivered" mode
  - [x] Test executable default mode behavior (should be "Delivered")
- [ ] (Optional) Add **end-to-end test** using dummy or sandbox iCloud
- [ ] Add all tests to CI/CD
- [x] Achieve ≥ **80% test coverage** for core sync logic (✅ **85.21%**
      achieved)

---

## 6️⃣ 🐧🪟 Cross-Platform Build

### 6.1 PyInstaller Configuration

- [x] Write **PyInstaller spec** for cross-platform builds:
  - [x] Create `icloud_photo_sync.spec` with proper data files inclusion
  - [x] Include repository `README.md` and `.env.example` as embedded resources
  - [x] Configure hiddenimports for keyring backends (Windows, macOS, Linux)
  - [x] Set up proper pathex and binaries configuration
  - [x] Ensure delivery artifacts resources are accessible in executable

### 6.2 Build Scripts and Commands

- [x] Create **Windows build script**:
  - [x] Add PowerShell script (`build_windows.ps1`) for Windows `.exe` generation
  - [x] Include dependency installation via `uv sync`
  - [x] Add PyInstaller execution with spec file
  - [x] Include post-build verification steps
  - [x] Add clean build option and output size reporting
- [x] Create **Linux build script**:
  - [x] Add shell script (`build_linux.sh`) for Linux executable generation
  - [x] Configure static linking options where possible
  - [x] Include dependency installation via `uv sync`
  - [x] Add PyInstaller execution with spec file
  - [x] Include system dependency checks and recommendations
- [x] Create **cross-platform test script**:
  - [x] Add Python script (`test_build.py`) for executable verification
  - [x] Include startup tests, dependency checks, and resource validation
  - [x] Test delivered mode behavior and settings folder creation
  - [x] Support both quick tests and comprehensive test suite

### 6.3 Resource Management in Builds

- [x] Implement **delivery artifacts integration**:
  - [x] Ensure repository `README.md` is embedded in executable
  - [x] Ensure repository `.env.example` is embedded as template source
  - [x] Configure path resolution for PyInstaller frozen mode vs development
  - [x] Test resource access in both development and packaged modes
- [ ] Validate **resource extraction**:
  - [ ] Test README.md extraction to settings folder in "Delivered" mode
  - [ ] Test settings.ini.template creation from embedded .env.example
  - [ ] Verify file permissions and accessibility after extraction

### 6.4 Cross-Platform Testing

- [ ] Test **Windows builds**:
  - [x] Create automated testing tools (`test_build.py`)
  - [ ] Verify `.exe` runs on Windows 10/11
  - [ ] Test delivery artifacts creation on first run
  - [ ] Verify settings folder detection (%USERPROFILE%\\AppData\\Local\\FotoPool)
  - [ ] Test file copying and user notifications
- [ ] Test **Linux builds**:
  - [x] Create automated testing tools (`test_build.py`)
  - [ ] Verify executable runs on Ubuntu/Debian
  - [ ] Test delivery artifacts creation on first run
  - [ ] Verify settings folder detection (~/.local/share/foto-pool)
  - [ ] Test file copying and user notifications
- [ ] Test **cross-platform compatibility**:
  - [x] Create comprehensive test framework
  - [ ] Verify same behavior across platforms
  - [ ] Test environment variable expansion (Windows vs Linux)
  - [ ] Validate path separators and file permissions

### 6.5 Feature Testing in Packaged Builds

- [ ] Test **2FA system in executables**:
  - [ ] Verify local web server startup in packaged builds
  - [ ] Test port conflict handling in executables
  - [ ] Validate session storage and retrieval
  - [ ] Ensure web interface accessibility (localhost binding)
- [ ] Test **Pushover notifications in executables**:
  - [ ] Verify API calls work from packaged builds
  - [ ] Test notification delivery for 2FA triggers
  - [ ] Validate error notifications for unhandled exceptions
  - [ ] Test device-specific notification targeting
- [ ] Test **keyring integration in executables**:
  - [ ] Verify Windows Credential Manager access
  - [ ] Verify Linux Secret Service integration
  - [ ] Test credential storage and retrieval
  - [ ] Validate fallback to environment variables

### 6.6 Build Optimization and Performance

- [x] Create **build documentation**:
  - [x] Add comprehensive BUILD.md with instructions and troubleshooting
  - [x] Document build script options and customization
  - [x] Include distribution packaging examples
- [ ] Optimize **executable size**:
  - [ ] Exclude unnecessary dependencies from builds
  - [ ] Use UPX compression where appropriate
  - [ ] Test startup performance of compressed executables
- [ ] Optimize **startup time**:
  - [ ] Profile executable startup sequence
  - [ ] Minimize import overhead in frozen builds
  - [ ] Test cold start vs warm start performance
- [ ] Validate **resource usage**:
  - [ ] Monitor memory usage in packaged builds
  - [ ] Test long-running continuous mode resource consumption
  - [ ] Verify proper cleanup on application exit

### 6.7 Build System Status

✅ **Completed Infrastructure:**
- PyInstaller spec file with resource embedding
- Windows PowerShell build script with options
- Linux bash build script with dependency checks
- Cross-platform test framework for verification
- Comprehensive build documentation and troubleshooting guide

🔄 **Ready for Testing:**
- Manual build testing on Windows and Linux systems
- Delivery artifacts verification in packaged executables
- 2FA and Pushover functionality validation in builds
- Performance profiling and optimization

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
- [x] Add **delivery artifacts configuration**:
  - [x] Add operating mode configuration ("InDevelopment" vs "Delivered")
  - [x] Set default operating mode to "InDevelopment" for development environment
  - [x] Implement settings folder detection for "Delivered" mode
  - [x] Implement required files check (README.md, settings.ini.template, settings.ini)
  - [x] Add file copying mechanism for missing delivery artifacts
  - [x] Implement program termination with user notification when files are missing
  - [x] Add automatic copying of README.md and settings.ini.template on each "Delivered" mode startup
  - [x] Ensure settings.ini is never overwritten in "Delivered" mode
  - [x] Set "Delivered" mode as default for executable packages (PyInstaller)
- [ ] Add **album filtering configuration**:
  - [ ] Add `include_personal_albums` boolean parameter to .env template
  - [ ] Add `personal_album_names_to_include` comma-separated list parameter
  - [ ] Add `include_shared_albums` boolean parameter to .env template
  - [ ] Add `shared_album_names_to_include` comma-separated list parameter
  - [ ] Update .env.example with album filtering examples
  - [ ] Add configuration validation for album parameters
- [x] Add **database path configuration**:
  - [x] Add database location parameter to .env template
  - [x] Support relative and absolute paths in database configuration
  - [x] Document environment variable usage (e.g.,
        %LOCALAPPDATA%/foto_pool/deletion_tracker)
  - [x] Add cross-platform environment variable mapping documentation
  - [x] Set default database path to ".data" in configuration examples
- [ ] Ensure credentials are not bundled in builds
- [x] Implement robust **logging** to console & file

---

## 9️⃣ 📜 Documentation

- [ ] Write **user guide**:
  - [ ] How to install (Windows & Linux)
  - [ ] How to configure sync dir & credentials
  - [ ] How to configure **database location**
  - [ ] How to use environment variables in database path
  - [ ] Cross-platform database path configuration examples
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
  - [ ] **Database path configuration** works with relative/absolute paths
  - [ ] **Environment variables** in database paths work cross-platform
  - [x] **Delivery artifacts management** works correctly:
    - [x] Executable defaults to "Delivered" mode
    - [x] Settings folder is created/detected correctly
    - [x] Required files (README.md, settings.ini.template, settings.ini) are copied when missing
    - [x] User receives clear notification about copied files and their purpose
    - [x] Program terminates gracefully after copying files with instruction to adjust settings.ini
    - [x] README.md and settings.ini.template are updated on each startup
    - [x] Existing settings.ini is preserved and never overwritten
  - [ ] No credentials leaked in binary
  - [ ] Handles credential failures gracefully
- [ ] Test Linux executable:
  - [ ] All 2FA features work on Linux
  - [ ] All album filtering features work on Linux
  - [ ] Cross-platform session storage works
  - [ ] Cross-platform album-aware database works
  - [ ] Cross-platform database path configuration works correctly
  - [x] **Delivery artifacts management** works on Linux:
    - [x] Cross-platform settings folder detection works
    - [x] File copying works with appropriate permissions
    - [x] User notifications work correctly on Linux terminal

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
- ✔️ **Delivery artifacts management** works correctly:
  - ✔️ Operating modes ("InDevelopment"/"Delivered") are properly implemented
  - ✔️ Executable packages default to "Delivered" mode
  - ✔️ Required files are automatically deployed in "Delivered" mode
  - ✔️ User receives clear guidance for first-time setup
  - ✔️ Template files are kept up-to-date automatically
  - ✔️ User settings are preserved across updates

---

**References:**

- [pyicloud](https://pypi.org/project/pyicloud/)
- [uv](https://docs.astral.sh/uv/)
- [uv Monorepo Guide](https://github.com/JasperHG90/uv-monorepo)
- [PyInstaller CI/CD Guide](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)
- [APT Repo Guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
- [WinGetCreate](https://techwatching.dev/posts/wingetcreate)

---
