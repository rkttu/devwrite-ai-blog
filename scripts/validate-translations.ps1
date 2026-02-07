#!/usr/bin/env pwsh
<#
.SYNOPSIS
    번역본 일관성을 검증하는 스크립트

.DESCRIPTION
    - translationKey가 모든 언어에서 일치하는지 확인
    - slug가 모든 언어에서 일치하는지 확인
    - 누락된 번역본 확인
    - Hero 이미지 존재 여부 확인

.EXAMPLE
    .\scripts\validate-translations.ps1
#>

$ErrorActionPreference = "Stop"
$ContentRoot = Join-Path $PSScriptRoot "..\content"
$StaticRoot = Join-Path $PSScriptRoot "..\static"
$Languages = @("ko", "en", "ja")
$BaseLanguage = "ko"

$errors = @()
$warnings = @()

Write-Host "🔍 Validating translations..." -ForegroundColor Cyan

# 모든 포스트 수집
$posts = @{}
foreach ($lang in $Languages) {
    $postsDir = Join-Path $ContentRoot "$lang\posts"
    if (Test-Path $postsDir) {
        Get-ChildItem -Path $postsDir -Directory | ForEach-Object {
            $indexFile = Join-Path $_.FullName "index.md"
            if (Test-Path $indexFile) {
                $content = Get-Content $indexFile -Raw
                
                # Front matter 파싱 (간단한 YAML 파싱)
                if ($content -match "(?s)^---\s*\n(.+?)\n---") {
                    $frontMatter = $Matches[1]
                    
                    $translationKey = if ($frontMatter -match 'translationKey:\s*["\x27]?([^"\x27\n]+)["\x27]?') { $Matches[1].Trim() } else { $null }
                    $slug = if ($frontMatter -match 'slug:\s*["\x27]?([^"\x27\n]+)["\x27]?') { $Matches[1].Trim() } else { $null }
                    $coverImage = if ($frontMatter -match 'image:\s*["\x27]?([^"\x27\n]+)["\x27]?') { $Matches[1].Trim() } else { $null }
                    
                    $key = $_.Name
                    if (-not $posts.ContainsKey($key)) {
                        $posts[$key] = @{}
                    }
                    $posts[$key][$lang] = @{
                        Path = $indexFile
                        TranslationKey = $translationKey
                        Slug = $slug
                        CoverImage = $coverImage
                    }
                }
            }
        }
    }
}

# 검증
foreach ($postName in $posts.Keys) {
    $post = $posts[$postName]
    
    # 1. 기본 언어(ko)에 존재하는지 확인
    if (-not $post.ContainsKey($BaseLanguage)) {
        $errors += "❌ [$postName] 기본 언어($BaseLanguage) 버전이 없습니다."
        continue
    }
    
    $basePost = $post[$BaseLanguage]
    
    # 2. translationKey 확인
    if (-not $basePost.TranslationKey) {
        $errors += "❌ [$postName] translationKey가 없습니다. (ko)"
    }
    
    # 3. slug 확인
    if (-not $basePost.Slug) {
        $errors += "❌ [$postName] slug가 없습니다. (ko)"
    }
    
    # 4. 번역본 확인
    foreach ($lang in $Languages) {
        if ($lang -eq $BaseLanguage) { continue }
        
        if (-not $post.ContainsKey($lang)) {
            $warnings += "⚠️  [$postName] $lang 번역본이 없습니다."
        } else {
            $langPost = $post[$lang]
            
            # translationKey 일치 확인
            if ($langPost.TranslationKey -ne $basePost.TranslationKey) {
                $errors += "❌ [$postName] translationKey 불일치: ko='$($basePost.TranslationKey)' vs $lang='$($langPost.TranslationKey)'"
            }
            
            # slug 일치 확인
            if ($langPost.Slug -ne $basePost.Slug) {
                $errors += "❌ [$postName] slug 불일치: ko='$($basePost.Slug)' vs $lang='$($langPost.Slug)'"
            }
        }
    }
    
    # 5. Hero 이미지 확인
    if ($basePost.CoverImage) {
        $imagePath = Join-Path $StaticRoot $basePost.CoverImage
        if (-not (Test-Path $imagePath)) {
            $warnings += "⚠️  [$postName] Hero 이미지를 찾을 수 없습니다: $($basePost.CoverImage)"
        }
    }
}

# 결과 출력
Write-Host ""
Write-Host "=" * 50

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ 모든 검증을 통과했습니다!" -ForegroundColor Green
} else {
    if ($errors.Count -gt 0) {
        Write-Host "`n❌ 오류 ($($errors.Count)개):" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️  경고 ($($warnings.Count)개):" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    }
}

Write-Host ""

# 오류가 있으면 exit code 1
if ($errors.Count -gt 0) {
    exit 1
}
