# 📄 Software Specification — iCloud Photo Sync Tool

## Overview

The goal is to develop a **Python-based tool** that synchronizes photos from an iCloud account to a local directory. It must **only download new photos** and must respect local deletions — i.e., if a photo is deleted locally, it must not be re-synced. The tool **must not delete any photos** from the iCloud account.

The project will be managed as a **mono-repo** using **uv** for dependency management, hosted on **GitHub**, and packaged into a standalone **Windows `.exe`** using **PyInstaller**. CI/CD will build and release the executable automatically using **GitHub Actions**.

---

## ✅ Requirements

### 1️⃣ Functional Requirements

1. **Photo Sync**  
   - Sync photos from iCloud to a local directory.  
   - Only download photos that do not yet exist locally.  
   - If a photo is deleted locally, it must **not** be re-downloaded on the next sync.  
   - Locally deleted photos must **not** be removed from iCloud.
   - shall run on windows and linux
   - credentials shall be storable via keyrind or as environment variable
   - if 2FA authentication is required, the user shall be notified via pushover
   - The pushover notification shall include a http-link to a local address, see next requirement
   - A local webserver shall be started, which enable the user to trigger a new F2A-request via a button
   - When the button is actuated, a F2A authentication session shall be started, which in turn ask for a 2FA key. The user shall be able to enter the key in the web-interface of the locally started webserver.
   - The http site needn't be secured as the server is running only in a private network.

2. **Local Deletion Tracking**  
   - Persistently track which files have been deleted locally to avoid re-downloading.  
   - Use a local lightweight database (e.g., SQLite or a JSON file) for tracking.

3. **Idempotent Runs**  
   - Running the tool multiple times must not create duplicate files or unintended deletions.

---

### 2️⃣ Non-Functional Requirements

4. **Programming Language**  
   - Python.

5. **iCloud API Integration**  
   - Use the `pyicloud` package: [https://pypi.org/project/pyicloud/](https://pypi.org/project/pyicloud/)

6. **Package Management**  
   - Use `uv` for managing dependencies: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)  
   - Maintain all dependencies in `pyproject.toml`.

7. **Repository Structure**  
   - Mono-repo structure as per the guide: [https://github.com/JasperHG90/uv-monorepo](https://github.com/JasperHG90/uv-monorepo)

8. **Version Control**  
   - Git repository, hosted on GitHub.

9. **Executable Packaging**  
   - Build a standalone Windows .exe and a Linux executable using PyInstaller.
   - The Linux build must be statically linked if possible, or provide clear runtime requirements.

10. **CI/CD Pipeline**  
   - Use GitHub Actions for building, testing, packaging, and releasing the executables for both Windows and Linux.
   - Follow this guide for PyInstaller CI/CD: [https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)

---

### 3️⃣ Optional but Recommended

- Configurable local sync directory & secure credentials.
- Detailed logging to console & file.
- Dry-run mode for testing sync logic.
- Cross-platform support for running directly with Python.
- Clear user documentation.

---

## ✅ 4️⃣ Testing Requirements

**Purpose:** Ensure high reliability, protect iCloud data integrity, and verify that local deletion tracking works as specified.

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

3. **End-to-End Tests** *(Optional but recommended)*  
   - Run the tool in a test mode against a dummy or sandboxed iCloud account (or fully mocked).  
   - Verify that:
     - New photos are downloaded.
     - Local deletions are respected.
     - No unintended deletions occur on iCloud.

4. **Test Automation**  
   - Tests must run automatically in the CI/CD pipeline on each pull request and push.
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
  - The linux package shall be published as APT repository, see [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
  - The required APT-package-structure shall be taken into account, see [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
  - The windows package shall be published as WinGet package, see https://techwatching.dev/posts/wingetcreate
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

- **pyicloud**: [https://pypi.org/project/pyicloud/](https://pypi.org/project/pyicloud/)  
- **uv**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)  
- **uv Monorepo Guide**: [https://github.com/JasperHG90/uv-monorepo](https://github.com/JasperHG90/uv-monorepo)  
- **PyInstaller CI/CD Guide**: [https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278](https://ragug.medium.com/ci-cd-pipeline-for-pyinstaller-on-github-actions-for-windows-7f8274349278)
- **APT Repository**: [https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository](https://www.ms8.com/how-to-submit-your-application-to-the-official-apt-repository)
---

**End of Specification**
