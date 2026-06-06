param(
  [string]$Message = "Update BESS shows $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
  [string]$RepoName = "bess_shows",
  [ValidateSet("private", "public")]
  [string]$Visibility
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Run-Git {
  & git @args
  if ($LASTEXITCODE -ne 0) {
    throw "Git command failed: git $($args -join ' ')"
  }
}

function Run-Command {
  param(
    [string]$Exe,
    [string[]]$CommandArgs,
    [string]$FailureMessage
  )

  & $Exe @CommandArgs
  if ($LASTEXITCODE -ne 0) {
    throw $FailureMessage
  }
}

function Get-GhCommand {
  $gh = Get-Command gh -ErrorAction SilentlyContinue
  if ($gh) {
    return $gh.Source
  }

  $cmderGh = "D:\softs1\cmder\gh.cmd"
  if (Test-Path $cmderGh) {
    return $cmderGh
  }

  throw "GitHub CLI was not found. Install gh or update this script with the gh path."
}

function Assert-NoStagedSensitiveFiles {
  $blockedRoots = @(
    ".idea",
    ".vscode",
    ".spyproject",
    ".ipynb_checkpoints",
    "PVsyst数据",
    "all_data_shows",
    "__pycache__"
  )
  $blockedExtensions = @(".xlsx", ".xls", ".html", ".ipynb")

  $stagedFiles = & git diff --cached --name-only
  if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect staged files."
  }

  $blockedFiles = @()
  foreach ($file in $stagedFiles) {
    $normalized = $file -replace "\\", "/"
    $extension = ""
    if ($normalized -match "(\.[^./]+)$") {
      $extension = $Matches[1]
    }
    $topLevel = ($normalized -split "/")[0]
    if (($blockedRoots -contains $topLevel) -or ($blockedExtensions -contains $extension) -or ($normalized.StartsWith("~$"))) {
      $blockedFiles += $file
    }
  }

  if ($blockedFiles.Count -gt 0) {
    foreach ($file in $blockedFiles) {
      & git restore --staged -- $file
    }
    throw "Refusing to commit generated/local files: $($blockedFiles -join ', ')"
  }
}

$ghExe = Get-GhCommand

if (-not (Test-Path ".git")) {
  Write-Host "Initializing git repository..."
  Run-Git init -b main
}

Write-Host "Checking GitHub CLI authentication..."
& $ghExe auth status
if ($LASTEXITCODE -ne 0) {
  throw "GitHub CLI is not authenticated. Run: gh auth login"
}

Write-Host "Checking repository content..."
Run-Git diff --check

Write-Host "Running Python syntax checks..."
Run-Command -Exe "python" -CommandArgs @("-m", "compileall", "-q", ".") -FailureMessage "Python syntax check failed."

Write-Host "Staging changes..."
Run-Git add --all -- .
Assert-NoStagedSensitiveFiles

& git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
  Write-Host "Creating commit: $Message"
  Run-Git commit -m $Message
} elseif ($LASTEXITCODE -ne 0) {
  throw "Unable to inspect staged changes."
} else {
  Write-Host "No new changes to commit."
}

$remotes = & git remote
if ($LASTEXITCODE -ne 0) {
  throw "Unable to inspect git remotes."
}
$hasOrigin = $remotes -contains "origin"

if (-not $hasOrigin) {
  if (-not $Visibility) {
    throw "GitHub repository does not exist yet. Re-run with -Visibility private or -Visibility public."
  }

  Write-Host "Creating GitHub repository '$RepoName' as $Visibility..."
  & $ghExe repo create $RepoName "--$Visibility" --source . --remote origin
  if ($LASTEXITCODE -ne 0) {
    throw "GitHub repository creation failed."
  }
}

$proxy = "http://127.0.0.1:7897"
$githubUser = "bhcgdh"
$proxyListening = Get-NetTCPConnection -State Listen -LocalPort 7897 -ErrorAction SilentlyContinue
if (-not $proxyListening) {
  Write-Host "Local proxy 127.0.0.1:7897 is not listening. Pushing without proxy..."
  Run-Git push -u origin main
} else {
  Write-Host "Pushing through local proxy..."
  $env:GCM_INTERACTIVE = "Never"
  Run-Git -c "credential.username=$githubUser" -c "credential.interactive=never" -c "http.proxy=$proxy" -c "https.proxy=$proxy" push -u origin main
}

Write-Host "Push completed."
Run-Git status -sb
Run-Git log -1 --oneline --decorate
