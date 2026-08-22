#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "validate_translations.py"

python $ScriptPath
exit $LASTEXITCODE
