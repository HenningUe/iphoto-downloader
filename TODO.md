# ✅ TODO.md — iCloud Photo Sync Tool

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

## 2️⃣ ⚙️ Core Sync Logic

- [x] Implement **iCloud authentication** using `pyicloud`
- [x] Implement **configurable local sync directory**
- [x] Develop logic to:
  - [x] List all photos in iCloud
  - [x] Identify which photos already exist locally
  - [x] Check local deletion database for deleted photos
  - [x] Download only new photos
- [x] Ensure **idempotent runs** (no duplicates)
- [x] Add **dry-run mode** to show sync actions without modifying files

---

## 3️⃣ 🗂️ Local Deletion Tracking

- [x] Design lightweight **SQLite** or **JSON-based** local deletion tracker
- [x] Create functions to:
  - [x] Record deleted files when missing locally
  - [x] Persistently update tracker on each sync
- [x] Integrate deletion tracker with sync logic

---

## 4️⃣ 🧪 Tests

- [x] Write **unit tests** for:
  - [x] Photo listing & new photo detection
  - [x] Local deletion tracking logic
  - [x] Database read/write functions
  - [x] File system utilities
- [x] Write **integration tests** with mocked `pyicloud`:
  - [x] Simulate new photos, already downloaded photos, deleted photos
  - [x] Simulate API errors & retry logic
- [ ] (Optional) Add **end-to-end test** using dummy or sandbox iCloud
- [ ] Add all tests to CI/CD
- [x] Achieve ≥ **80% test coverage** for core sync logic (✅ **85.21%** achieved)

---

## 5️⃣ 🐧🪟 Cross-Platform Build

- [ ] Write **PyInstaller spec** for Windows `.exe`
- [ ] Write **PyInstaller spec** for Linux executable (consider static linking if possible)
- [ ] Test builds locally on Windows and Linux

---

## 6️⃣ 🔁 CI/CD Pipeline (GitHub Actions)

- [ ] Create **CI workflow**:
  - [ ] Install dependencies using `uv`
  - [ ] Run unit & integration tests
  - [ ] Run `ruff` and `mypy`
  - [ ] Build `.exe` for Windows and executable for Linux
  - [ ] Package Linux build for **APT repo** ([APT guide](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository))
  - [ ] Package Windows build for **WinGet** ([WinGetCreate](https://techwatching.dev/posts/wingetcreate))
  - [ ] Publish releases automatically

---

## 7️⃣ 🧩 Configuration & Security

- [x] Add example `.env` template for credentials
- [x] Support configurable local sync directory
- [ ] Ensure credentials are not bundled in builds
- [x] Implement robust **logging** to console & file

---

## 8️⃣ 📜 Documentation

- [ ] Write **user guide**:
  - [ ] How to install (Windows & Linux)
  - [ ] How to configure sync dir & credentials
  - [ ] How to run dry-run mode
  - [ ] How local deletion tracking works
- [ ] Include usage examples & troubleshooting tips

---

## 9️⃣ ✅ Manual Verification

- [ ] Test `.exe` on Windows:
  - [ ] App runs and syncs as expected
  - [ ] No credentials leaked in binary
  - [ ] Handles credential failures gracefully

---

## 1️⃣0️⃣ 🚀 Release

- [ ] Tag a versioned release on GitHub
- [ ] Verify Linux package published to **APT repo**
- [ ] Verify Windows build published to **WinGet**
- [ ] Test install & run on fresh Windows/Linux machine

---

## 🎉 DONE when:

- ✔️ No re-downloads of locally deleted photos  
- ✔️ No accidental deletions on iCloud  
- ✔️ Idempotent sync runs  
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
