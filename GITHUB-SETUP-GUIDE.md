# GitHub Manual Setup Guide

**Time Required:** ~15 minutes
**Prerequisite:** Repository admin access for `FAIR-DM/fairdm`

---

## Step 1: Enable Auto-Merge (2 minutes)

Auto-merge allows the Dependabot auto-merge workflow to automatically merge PRs after CI passes.

### Navigation Path

```
Repository → Settings → General → Pull Requests
```

### Instructions

1. Go to your repository: `https://github.com/FAIR-DM/fairdm`

2. Click **Settings** (top navigation bar)

3. In the left sidebar, ensure you're on **General**

4. Scroll down to the **"Pull Requests"** section

5. Find the checkbox: **"Allow auto-merge"**
   - ✅ Check this box
   - Description: *"Pull requests can be merged automatically by users with write permissions using the GitHub CLI or API"*

6. Click **Save** (if a save button appears)

**Verification:** The checkbox should remain checked after page refresh.

---

## Step 2: Configure Branch Protection Rules (5 minutes)

Branch protection ensures code quality by requiring CI to pass before merging to main.

### Navigation Path

```
Repository → Settings → Branches → Branch protection rules
```

### Instructions

1. In **Settings**, click **Branches** in the left sidebar

2. Under "Branch protection rules", click **Add rule** (or edit existing `main` rule)

3. **Branch name pattern:** Enter `main`

4. Configure the following settings:

   **✅ Require a pull request before merging**
   - Leave "Require approvals" **UNCHECKED** (auto-merge workflow handles this)
   - ❌ Uncheck "Dismiss stale pull request approvals when new commits are pushed"

   **✅ Require status checks to pass before merging**
   - ✅ Check "Require branches to be up to date before merging"
   - In the search box that appears, type and add: **`CI Success`**
     - This is the final job name from `.github/workflows/ci.yml`
     - It ensures all CI jobs (lint, type-check, test) passed
   - **Do NOT** add individual job names (lint, test, etc.) - only `CI Success`

   **✅ Require conversation resolution before merging** (optional but recommended)

   **❌ Do NOT check "Require review from Code Owners"** (blocks auto-merge)

   **❌ Do NOT check "Require signed commits"** (unless you want this)

   **✅ Do not allow bypassing the above settings** (recommended)

5. Scroll to bottom and click **Create** (or **Save changes**)

**Verification:**

- Return to the Branches page
- You should see a rule for `main` listed
- Click "Edit" to verify `CI Success` is in the required status checks

---

## Step 3: Verify/Configure Repository Secrets (3 minutes)

Secrets are used by workflows for external service authentication.

### Navigation Path

```
Repository → Settings → Secrets and variables → Actions
```

### Instructions

1. In **Settings**, expand **Secrets and variables** in the left sidebar

2. Click **Actions**

3. You should see the **"Repository secrets"** section

4. **Verify these secrets exist:**

   | Secret Name | Purpose | How to Get |
   |------------|---------|------------|
   | `CODECOV_TOKEN` | Upload coverage reports | CodeCov dashboard → fairdm project → Settings → Copy token |
   | `DOCKERHUB_TOKEN` | *(Optional - skip if not using Docker Hub)* | Docker Hub → Account Settings → Security → New Access Token |
   | `DOCKERHUB_USERNAME` | *(Optional - skip if not using Docker Hub)* | Your Docker Hub username |

5. **To add a missing secret:**
   - Click **New repository secret**
   - **Name:** Enter the secret name exactly (e.g., `CODECOV_TOKEN`)
   - **Value:** Paste the token value
   - Click **Add secret**

### Getting CodeCov Token

1. Go to <https://codecov.io/>
2. Sign in with GitHub
3. Find your `FAIR-DM/fairdm` project
4. Click **Settings** → **General**
5. Copy the **Repository Upload Token**
6. Add it as `CODECOV_TOKEN` in GitHub

**Note:** If you don't have CodeCov set up yet:

- The CI workflow will still work (it's configured with `fail_ci_if_error: false`)
- You just won't get coverage reports
- You can add this later

---

## Step 4: Configure PyPI Trusted Publishing (5 minutes)

Trusted publishing allows GitHub Actions to publish to PyPI without storing a password/token.

### Navigation Path

```
PyPI → Account Settings → Publishing
```

### Instructions

1. **Go to PyPI:** <https://pypi.org/>

2. **Sign in** to your PyPI account

3. Click your username (top right) → **Account settings**

4. In the left sidebar, click **Publishing**

5. Scroll to **"Pending publishers"** section

6. Click **Add a new pending publisher**

7. Fill in the form:

   ```
   PyPI Project Name: fairdm
   Owner: FAIR-DM
   Repository name: fairdm
   Workflow name: release.yml
   Environment name: pypi
   ```

8. Click **Add**

**Verification:**

- You should see `fairdm` listed under "Pending publishers"
- After your first successful release, it will move to "Current publishers"

### Important Notes

- **First release:** The project must already exist on PyPI, OR you must create it with the first upload
- **If project doesn't exist yet:** You may need to do the first upload manually:

  ```bash
  poetry build
  poetry publish
  ```

- **After first release:** All subsequent releases use trusted publishing automatically

---

## Step 5: Create Release Environment (Optional but Recommended) (2 minutes)

The release workflow references a `pypi` environment. Creating it adds an extra layer of control.

### Navigation Path

```
Repository → Settings → Environments
```

### Instructions

1. In **Settings**, click **Environments** in the left sidebar

2. Click **New environment**

3. **Name:** Enter `pypi` (exactly as shown)

4. Click **Configure environment**

5. **Optional configurations:**
   - **Required reviewers:** Add yourself if you want manual approval before PyPI releases
   - **Wait timer:** Leave at 0 (no delay)
   - **Deployment branches:** Select "Selected branches" → Add `main`

6. Click **Save protection rules**

**Why do this:**

- Adds protection for production deployments
- You can require manual approval for releases
- Restricts releases to only come from `main` branch

**If you skip this:**

- Workflow will still work
- Just won't have the extra protection layer

---

## Step 6: Optional - Remove/Disable Docker Publishing

Since you're using GitHub Packages instead of Docker Hub, you have two options:

### Option A: Disable Docker Job in Release Workflow (Recommended)

Edit `.github/workflows/release.yml`:

**Find this section (around line 130):**

```yaml
  docker:
    name: Publish to Docker Hub
    runs-on: ubuntu-latest
    needs: [build, github-release]
```

**Add a condition to skip it:**

```yaml
  docker:
    name: Publish to Docker Hub
    runs-on: ubuntu-latest
    needs: [build, github-release]
    if: false  # Disabled - using GitHub Packages instead
```

### Option B: Replace with GitHub Container Registry

If you want to publish Docker images to GitHub Packages (ghcr.io):

1. **Generate GitHub Personal Access Token:**
   - Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `write:packages` scope
   - Add as repository secret: `GHCR_TOKEN`

2. **Update release.yml** - replace Docker job with:

```yaml
  docker:
    name: Publish to GitHub Container Registry
    runs-on: ubuntu-latest
    needs: [build, github-release]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/fair-dm/fairdm
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### Option C: Keep As-Is But Don't Configure Docker Hub

- The release workflow will fail on the Docker job
- GitHub Release and PyPI publishing will still succeed
- You can ignore the Docker failure

---

## Step 7: Test the Setup (5 minutes)

### Test 1: CI Workflow

1. **Create a test branch:**

   ```bash
   git checkout -b test/github-setup
   ```

2. **Make a trivial change:**

   ```bash
   echo "# Test GitHub setup" >> README.md
   git add README.md
   git commit -m "test: verify CI workflow"
   git push origin test/github-setup
   ```

3. **Create a pull request** from GitHub UI

4. **Verify:**
   - ✅ CI workflow starts automatically
   - ✅ Lint job passes
   - ✅ Type-check job passes
   - ✅ Test job passes
   - ✅ `CI Success` job passes
   - ✅ PR shows "Required checks passed"
   - Note: Workflows use your existing `SamuelJennings/cached-poetry-action@v1`

5. **Merge the PR** (or close it if it's just a test)

### Test 2: Auto-Merge (After Dependabot Creates PRs)

1. **Wait for Dependabot** to create a PR (runs every Monday)
   - Or manually trigger: Repository → Insights → Dependency graph → Dependabot → "Check for updates"

2. **When a Dependabot PR appears:**
   - Check for auto-merge comment: "✅ Auto-approving: [reason]"
   - OR check for manual review comment: "👀 Manual Review Required"

3. **Verify auto-merge behavior:**
   - Safe updates (dev deps, patches): Should auto-merge after CI
   - Critical updates (Django, Celery): Should have manual review comment

### Test 3: Release Workflow (Dry Run)

**Option A: Use workflow_dispatch**

1. Go to Actions → Release workflow
2. Click "Run workflow"
3. Enter a test tag like `v2025.0-test`
4. Click "Run workflow"
5. Monitor the build and verify jobs complete

**Option B: Create a test tag**

```bash
git tag v2025.0-test
git push origin v2025.0-test
```

**Warning:** This will actually publish to PyPI if configured!

- Use workflow_dispatch first to test without publishing
- Or use a prerelease tag like `v2025.0-alpha1`

---

## Common Issues & Solutions

### Issue: "CI Success" status check not found

**Cause:** The check name is case-sensitive and must match exactly.

**Solution:**

1. Run the CI workflow on a PR first
2. Then add it as a required check
3. Or manually type `CI Success` exactly

### Issue: Auto-merge not working

**Possible causes:**

1. "Allow auto-merge" not enabled → Enable in Settings → General
2. Branch protection requiring approvals → Remove approval requirement
3. CI not passing → Check workflow logs
4. Update is for a critical package → This is expected, manual review required

### Issue: PyPI publishing fails

**Causes:**

1. Project doesn't exist on PyPI yet → Do first release manually
2. Trusted publisher not configured → Follow Step 4 above
3. Wrong environment name → Must be exactly `pypi`

### Issue: Secrets not available in workflow

**Cause:** Secrets are only available in specific contexts.

**Solution:**

- `GITHUB_TOKEN` is automatic, no setup needed
- Other secrets must be added in Settings → Secrets and variables → Actions

---

## Summary Checklist

Before considering setup complete:

- [ ] Auto-merge enabled in repository settings
- [ ] Branch protection rule for `main` configured with `CI Success` required
- [ ] `CODECOV_TOKEN` secret added (or CodeCov configured)
- [ ] PyPI trusted publishing configured
- [ ] `pypi` environment created (optional)
- [ ] Docker publishing disabled or configured for GitHub Packages
- [ ] Test PR created and CI passed
- [ ] Dependabot auto-merge tested (can wait for first Monday)
- [ ] Release workflow tested with workflow_dispatch

---

## Next Steps After Setup

1. **Monitor first week:**
   - Check Dependabot PRs on Monday
   - Verify which ones auto-merge vs. need review
   - Adjust auto-merge criteria if needed

2. **First release:**
   - Create a proper version tag: `v2025.1`
   - Verify GitHub release created
   - Verify PyPI package published
   - Check changelog generation

3. **Regular maintenance:**
   - Weekly: Review security scan results
   - Monthly: Check auto-merge statistics
   - Per release: Verify multi-platform publishing

---

## Additional Resources

- **GitHub Actions Docs:** <https://docs.github.com/en/actions>
- **Branch Protection:** <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches>
- **PyPI Trusted Publishing:** <https://docs.pypi.org/trusted-publishers/>
- **Auto-merge:** <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request>

---

**Questions or Issues?** Check the workflow logs in GitHub Actions for detailed error messages.
