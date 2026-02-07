#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Hero 이미지를 WebP 형식으로 변환하고 리사이즈하는 래퍼 스크립트

.DESCRIPTION
    Python 스크립트 optimize_images.py를 호출합니다.
    Pillow 패키지가 필요합니다: pip install Pillow

.PARAMETER Slug
    특정 포스트 슬러그의 이미지만 변환

.PARAMETER MaxWidth
    최대 이미지 너비 (기본값: 1200)

.PARAMETER Quality
    WebP 품질 (1-100, 기본값: 85)

.PARAMETER DeleteOriginals
    변환 후 원본 JPG/PNG 파일 삭제

.PARAMETER UpdateFrontmatter
    front matter의 cover.image 경로를 .webp로 업데이트

.EXAMPLE
    .\scripts\optimize-images.ps1
    .\scripts\optimize-images.ps1 -Slug "my-post"
    .\scripts\optimize-images.ps1 -DeleteOriginals -UpdateFrontmatter
#>

param(
    [string]$Slug,
    [int]$MaxWidth = 1200,
    [int]$Quality = 85,
    [switch]$DeleteOriginals,
    [switch]$UpdateFrontmatter
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "optimize_images.py"

$args = @()

if ($Slug) {
    $args += "--slug", $Slug
}

$args += "--max-width", $MaxWidth
$args += "--quality", $Quality

if ($DeleteOriginals) {
    $args += "--delete-originals"
}

if ($UpdateFrontmatter) {
    $args += "--update-frontmatter"
}

python $ScriptPath @args
