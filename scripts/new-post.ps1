#!/usr/bin/env pwsh
<#
.SYNOPSIS
    새 블로그 포스트를 생성하는 스크립트

.DESCRIPTION
    한국어 기본 포스트를 생성하고 필수 front matter를 설정합니다.

.PARAMETER Slug
    URL에 사용될 슬러그 (영문, 하이픈 사용)

.PARAMETER Title
    포스트 제목 (한국어)

.EXAMPLE
    .\scripts\new-post.ps1 -Slug "my-first-post" -Title "나의 첫 번째 포스트"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Slug,
    
    [Parameter(Mandatory=$true)]
    [string]$Title
)

$ErrorActionPreference = "Stop"
$ContentRoot = Join-Path $PSScriptRoot "..\content\ko\posts"
$PostPath = Join-Path $ContentRoot "$Slug.md"

# 이미 존재하는지 확인
if (Test-Path $PostPath) {
    Write-Host "❌ 이미 존재하는 포스트입니다: $PostPath" -ForegroundColor Red
    exit 1
}

# 날짜 생성
$Date = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"

# Front matter 템플릿
$Content = @"
---
title: "$Title"
date: $Date
draft: true
slug: "$Slug"
tags: []
categories: []
translationKey: "$Slug"
cover:
  image: ""
  alt: ""
tldr: ""
---

여기에 내용을 작성하세요.
"@

# 디렉터리 생성
$dir = Split-Path $PostPath -Parent
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# 파일 생성
$Content | Out-File -FilePath $PostPath -Encoding utf8

Write-Host "✅ 새 포스트가 생성되었습니다:" -ForegroundColor Green
Write-Host "   $PostPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "  1. 포스트 내용 작성"
Write-Host "  2. tags, categories 추가"
Write-Host "  3. tldr 작성"
Write-Host "  4. Hero 이미지 추가 (선택)"
Write-Host "  5. draft: false로 변경"
Write-Host "  6. 번역본 생성 (en, ja)"
