
This is the project TODO list for implementing the **iCloud Photo Sync Tool** as specified.

---

## 1️⃣ 📁 Project Setup

- [x] Create **GitHub repo** with mono-repo structure ([uv monorepo guide](https://github.com/JasperHG90/uv-monorepo))
- [x] Initialize **`pyproject.toml`** using `uv`
- [x] Add `pyicloud` dependency
- [x] Add linting tools: `ruff`, `mypy`
- [x] Add `.gitignore` for Python, build outputs, and virtual environments
- [x] Add `README.md` with project overview

---

## 2️⃣ ⚙️ Core  Logic

### 2.1 Core Sync Logic
- [x] Implement **iCloud authentication** using `pyicloud`
- [x] Implement **configurable local sync directory**
- [x] Develop logic to:
  - [x] List all photos in iCloud
  - [x] Identify which photos already exist locally
  - [x] Check local deletion database for deleted photos
  - [x] Download only new photos
- [x] Ensure **idempotent runs** (no duplicates)
- [x] Add **dry-run mode** to show sync actions without modifying files

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
- [ ] Add **session cleanup** for expired sessions

#### 2.2.5 🛡️ Security & Error Handling
- [ ] Implement **graceful error handling** for server startup failures
- [ ] Add **port availability checking** before server start
- [ ] Implement **session timeout** mechanisms
- [ ] Add **rate limiting** for 2FA attempts
- [ ] Ensure no sensitive data in logs

#### 2.2.6 📝 2FA Logging
- [ ] Add **2FA-specific logging** for debugging
- [ ] Log 2FA requests and session states (without sensitive data)
- [ ] Implement **audit trail** for 2FA sessions
- [ ] Add **structured logging** for 2FA events

### 2.3 Local Deletion Tracking
- [x] Design lightweight **SQLite** or **JSON-based** local deletion tracker
- [x] Create functions to:
  - [x] Record deleted files when missing locally
  - [x] Persistently update tracker on each sync
- [x] Integrate deletion tracker with sync logic

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
- [ ] (Optional) Add **end-to-end test** using dummy or sandbox iCloud
- [ ] Add all tests to CI/CD
- [x] Achieve ≥ **80% test coverage** for core sync logic (✅ **85.21%** achieved)

---

## 6️⃣ 🐧🪟 Cross-Platform Build

- [ ] Write **PyInstaller spec** for Windows `.exe`
- [ ] Write **PyInstaller spec** for Linux executable (consider static linking if possible)
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
  - [ ] Package Linux build for **APT repo** ([APT guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository))
  - [ ] Package Windows build for **WinGet** ([WinGetCreate](https://techwatching.dev/posts/wingetcreate))
  - [ ] Publish releases automatically

---

## 8️⃣ 🧩 Configuration & Security

- [x] Add example `.env` template for credentials
- [x] Support configurable local sync directory
- [x] Add **Pushover configuration** (API token, user key)
- [ ] Add **2FA web server configuration** (port range, bind address)
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
- [ ] Include usage examples & troubleshooting tips

---

## 1️⃣0️⃣ ✅ Manual Verification

- [ ] Test `.exe` on Windows:
  - [ ] App runs and syncs as expected
  - [ ] **2FA web server** starts correctly
  - [ ] **Pushover notifications** are sent
  - [ ] **2FA web interface** works properly
  - [ ] No credentials leaked in binary
  - [ ] Handles credential failures gracefully
- [ ] Test Linux executable:
  - [ ] All 2FA features work on Linux
  - [ ] Cross-platform session storage works

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
- ✔️ **2FA notifications via Pushover work**  
- ✔️ **Local web server for 2FA works**  
- ✔️ **2FA sessions are stored securely**  
- ✔️ `.exe` builds automatically and runs on Windows  
- ✔️ CI/CD builds, tests, packages, and releases  
- ✔️ Clear logs for all sync operations  
- ✔️ Versioned releases available to users  
- ✔️ Users can easily install & configure  

---

**References:**  
- [pyicloud](https://pypi.org/project/pyicloud/)  
- [uv](https://docs.astral.sh/uv/)  
- [uv Monorepo Guide](https://github.com/JasperHG90/uv-monorepo)  
- [PyInstaller CI/CD Guide](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)  
- [APT Repo Guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)  
- [WinGetCreate](https://techwatching.dev/posts/wingetcreate)

---