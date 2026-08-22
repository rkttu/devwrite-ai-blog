#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Unsplash에서 Hero 이미지를 다운로드하는 스크립트

.DESCRIPTION
    검색어를 기반으로 Unsplash Source에서 이미지를 다운로드합니다.

.PARAMETER Slug
    포스트 슬러그 (파일명으로 사용)

.PARAMETER Keywords
    Unsplash 검색 키워드 (쉼표로 구분)

.PARAMETER Width
    이미지 너비 (기본값: 1200)

.PARAMETER Height
    이미지 높이 (기본값: 630)

.EXAMPLE
    .\scripts\fetch-hero-image.ps1 -Slug "my-post" -Keywords "coding,programming"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Slug,
    
    [Parameter(Mandatory=$true)]
    [string]$Keywords,
    
    [int]$Width = 1200,
    [int]$Height = 630
)

$ErrorActionPreference = "Stop"
$ImagesDir = Join-Path $PSScriptRoot "..\assets\images\posts"
$OutputPath = Join-Path $ImagesDir "$Slug.jpg"

# 디렉터리 생성
if (-not (Test-Path $ImagesDir)) {
    New-Item -ItemType Directory -Path $ImagesDir -Force | Out-Null
}

# 이미 존재하는지 확인
if (Test-Path $OutputPath) {
    $overwrite = Read-Host "이미지가 이미 존재합니다. 덮어쓰시겠습니까? (y/N)"
    if ($overwrite -ne "y") {
        Write-Host "취소되었습니다." -ForegroundColor Yellow
        exit 0
    }
}

# Unsplash Source URL
$url = "https://source.unsplash.com/${Width}x${Height}/?$Keywords"

Write-Host "🖼️  Unsplash에서 이미지를 다운로드합니다..." -ForegroundColor Cyan
Write-Host "   URL: $url"

try {
    # 이미지 다운로드
    Invoke-WebRequest -Uri $url -OutFile $OutputPath -UseBasicParsing
    
    Write-Host "✅ 이미지가 저장되었습니다:" -ForegroundColor Green
    Write-Host "   $OutputPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Front matter에 추가:" -ForegroundColor Yellow
    Write-Host @"
cover:
  image: "images/posts/$Slug.jpg"
  alt: "이미지 설명을 입력하세요"
"@
} catch {
    Write-Host "❌ 이미지 다운로드 실패: $_" -ForegroundColor Red
    exit 1
}
