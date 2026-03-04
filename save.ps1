# Quick save script for ExcelToMif project (PowerShell)
# Usage: .\save.ps1 "commit message"

param(
    [Parameter(Mandatory = $true)]
    [string]$CommitMessage
)

git add .
git commit -m $CommitMessage
git push origin master

Write-Host "Changes saved and pushed to GitHub" -ForegroundColor Green
