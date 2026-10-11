
# ============================================================
# RECREATE GIT HISTORY - 27 COMMITS + SOURCE CODE SNAPSHOT
# ============================================================

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# 1. PROJECT CONFIGURATION
# ------------------------------------------------------------

$SourcePath = "C:\Users\Lebos\Music\Mindworx WM_03_WE01 Software development\WA0103\Nelly_dhlamini_WM03_WA0103.01_Source_Code_Files\codebase"

$TargetPath = "C:\Projects\MyProject-Recreated"

$AuthorName = "Nelly-Dhlamini"
$AuthorEmail = "Nellydhlamini34@gmail.com"

# ------------------------------------------------------------
# 2. VALIDATE SOURCE AND TARGET
# ------------------------------------------------------------

git --version

if ($LASTEXITCODE -ne 0) {
    throw "Git is not installed or not available in PATH."
}

if (-not (Test-Path -LiteralPath $SourcePath -PathType Container)) {
    throw "Source directory does not exist: $SourcePath"
}

# The target may already exist from the previous failed run.
# Only reuse it if it is an empty, uncommitted repository.

if (Test-Path -LiteralPath $TargetPath) {

    $ExistingItems = @(
        Get-ChildItem -LiteralPath $TargetPath -Force |
        Where-Object { $_.Name -ne ".git" }
    )

    if ($ExistingItems.Count -gt 0) {
        throw "Target contains files. Use a new target path."
    }

    if (Test-Path -LiteralPath (Join-Path $TargetPath ".git")) {

        $ExistingCommits = git -C $TargetPath rev-list --all --count 2>$null

        if ($LASTEXITCODE -eq 0 -and [int]$ExistingCommits -gt 0) {
            throw "Target already contains commits. Use a new target path."
        }
    }
}
else {
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
}

Set-Location $TargetPath

# ------------------------------------------------------------
# 3. INITIALIZE GIT
# ------------------------------------------------------------

if (-not (Test-Path ".git")) {
    git init

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to initialize Git repository."
    }
}

git config user.name "$AuthorName"
git config user.email "$AuthorEmail"

# Disable signing for reconstructed commits
git config commit.gpgsign false

# ------------------------------------------------------------
# 4. DEFINE THE 27 COMMITS
# ------------------------------------------------------------
# Use PSCustomObject instead of nested arrays.
# This prevents PowerShell from flattening the values.
#
# Dates use original Unix timestamps with +0200.
# Order follows the original supplied Git records.
# ------------------------------------------------------------

$Commits = @(
    [PSCustomObject]@{
        Timestamp = 1784718840
        Message = "Add project scaffold, .gitignore and package init"
    },
    [PSCustomObject]@{
        Timestamp = 1784978040
        Message = "Add domain models and enums"
    },
    [PSCustomObject]@{
        Timestamp = 1785237240
        Message = "Add repository abstraction and in-memory store"
    },
    [PSCustomObject]@{
        Timestamp = 1785496440
        Message = "Add validation service (FR-VAL-01/02)"
    },
    [PSCustomObject]@{
        Timestamp = 1791026040
        Message = "Add configurable fraud rules (FR-FRD-01/02/03)"
    },
    [PSCustomObject]@{
        Timestamp = 1791741074
        Message = "Add fraud scoring engine (FR-FRD-04)"
    },
    [PSCustomObject]@{
        Timestamp = 1789989240
        Message = "Add decision service (FR-DEC-01)"
    },
    [PSCustomObject]@{
        Timestamp = 1789730040
        Message = "Add settlement service (FR-DEC-02)"
    },
    [PSCustomObject]@{
        Timestamp = 1789470840
        Message = "Add alerting service (FR-ALR-01/02)"
    },
    [PSCustomObject]@{
        Timestamp = 1789211640
        Message = "Add notification service (FR-CSM-02)"
    },
    [PSCustomObject]@{
        Timestamp = 1788952440
        Message = "Add fraud case management (FR-CSM-01)"
    },
    [PSCustomObject]@{
        Timestamp = 1791741076
        Message = "Add immutable hash-chained audit trail (FR-AUD-01/02)"
    },
    [PSCustomObject]@{
        Timestamp = 1788693240
        Message = "Add role-based access control (FR-IAM-01)"
    },
    [PSCustomObject]@{
        Timestamp = 1791741076
        Message = "Add incident controls: kill switch + replay (FR-INC-01)"
    },
    [PSCustomObject]@{
        Timestamp = 1788434040
        Message = "Add transaction processor orchestration (FR-ING-01 + flow)"
    },
    [PSCustomObject]@{
        Timestamp = 1791741077
        Message = "Add demo runner wiring the services together"
    },
    [PSCustomObject]@{
        Timestamp = 1791741297
        Message = "Add pytest fixtures (wired system + seeded account)"
    },
    [PSCustomObject]@{
        Timestamp = 1787829240
        Message = "Add validation tests (FR-VAL)"
    },
    [PSCustomObject]@{
        Timestamp = 1791741298
        Message = "Add fraud rule tests (FR-FRD)"
    },
    [PSCustomObject]@{
        Timestamp = 1787570040
        Message = "Add scoring and decision tests (FR-FRD-04/FR-DEC-01)"
    },
    [PSCustomObject]@{
        Timestamp = 1787310840
        Message = "Add settlement and audit-integrity tests (FR-DEC-02/FR-AUD)"
    },
    [PSCustomObject]@{
        Timestamp = 1787051640
        Message = "Add RBAC and incident-control tests (FR-IAM/FR-INC)"
    },
    [PSCustomObject]@{
        Timestamp = 1786792440
        Message = "Add end-to-end processor flow tests"
    },
    [PSCustomObject]@{
        Timestamp = 1786533240
        Message = "Add SQL Server persistence schema (fds)"
    },
    [PSCustomObject]@{
        Timestamp = 1786274040
        Message = "Add SqlRepository - persist to SQL Server"
    },
    [PSCustomObject]@{
        Timestamp = 1786014840
        Message = "Add system factory (build processor from any repository)"
    },
    [PSCustomObject]@{
        Timestamp = 1785755640
        Message = "Add Streamlit UI driving the persisted system"
    }
)

if ($Commits.Count -ne 27) {
    throw "Expected 27 commits, found $($Commits.Count)."
}

# ------------------------------------------------------------
# 5. CONFIGURE AUTHOR AND COMMITTER
# ------------------------------------------------------------

$env:GIT_AUTHOR_NAME = $AuthorName
$env:GIT_AUTHOR_EMAIL = $AuthorEmail

$env:GIT_COMMITTER_NAME = $AuthorName
$env:GIT_COMMITTER_EMAIL = $AuthorEmail

# ------------------------------------------------------------
# 6. CREATE ALL 27 COMMITS
# ------------------------------------------------------------

Write-Host ""
Write-Host "Creating 27 Git commits..."
Write-Host ""

$Index = 0

foreach ($Commit in $Commits) {

    $Index++

    $Timestamp = [string]$Commit.Timestamp
    $Message = [string]$Commit.Message

    if ([string]::IsNullOrWhiteSpace($Message)) {
        throw "Commit message is empty at index $Index."
    }

    # Set author and committer timestamps
    $env:GIT_AUTHOR_DATE = "$Timestamp +0200"
    $env:GIT_COMMITTER_DATE = "$Timestamp +0200"

    # Create metadata-only commit
    git -c commit.gpgsign=false commit --allow-empty -m "$Message"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed creating commit $Index : $Message"
    }

    Write-Host "[$Index/27] $Message"
}

# ------------------------------------------------------------
# 7. CLEAR TEMPORARY GIT ENVIRONMENT VARIABLES
# ------------------------------------------------------------

@(
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_DATE"
) | ForEach-Object {
    Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}

# ------------------------------------------------------------
# 8. COPY SOURCE CODE
# ------------------------------------------------------------

Write-Host ""
Write-Host "Copying source code..."

$ExcludedDirectories = @(
    ".git",
    ".git-backup",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache"
)

Get-ChildItem -LiteralPath $SourcePath -Force | ForEach-Object {

    if ($_.Name -notin $ExcludedDirectories) {

        Copy-Item `
            -LiteralPath $_.FullName `
            -Destination $TargetPath `
            -Recurse `
            -Force
    }
}

# ------------------------------------------------------------
# 9. COMMIT SOURCE CODE SNAPSHOT
# ------------------------------------------------------------

Write-Host ""
Write-Host "Staging source files..."

git add -A

if ($LASTEXITCODE -ne 0) {
    throw "Failed to stage source files."
}

git diff --cached --quiet

if ($LASTEXITCODE -eq 1) {

    git -c commit.gpgsign=false commit `
        -m "Add reconstructed source snapshot"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create source snapshot commit."
    }
}
elseif ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect staged changes."
}
else {
    Write-Host "No source files were staged."
}

# ------------------------------------------------------------
# 10. VERIFY RECONSTRUCTED HISTORY
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================"
Write-Host "GIT HISTORY RECONSTRUCTION COMPLETE"
Write-Host "============================================"

Write-Host ""
Write-Host "Commit count:"

git rev-list --count HEAD

Write-Host ""
Write-Host "Full commit history:"

git log --reverse --format="%h | %an <%ae> | %aI | %s"

Write-Host ""
Write-Host "Latest commit details:"

git log -1 --format=fuller

Write-Host ""
Write-Host "Tracked files:"

git ls-files

Write-Host ""
Write-Host "Working tree status:"

git status --short

Write-Host ""
Write-Host "Repository location:"
Write-Host $TargetPath

Write-Host ""
Write-Host "Completed."
