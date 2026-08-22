#!/usr/bin/env pwsh

param(
    [Parameter(Mandatory=$true)]
    [string]$Slug,

    [Parameter(Mandatory=$true)]
    [string]$Title
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "new_post.py"

python $ScriptPath --slug $Slug --title $Title
exit $LASTEXITCODE
