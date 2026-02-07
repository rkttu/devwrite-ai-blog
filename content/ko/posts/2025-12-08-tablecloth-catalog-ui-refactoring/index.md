---
title: "테이블에서 카드로: 식탁보 카탈로그 UI의 현대화 여정"
date: 2025-12-08T00:00:00+09:00
draft: false
slug: "tablecloth-catalog-ui-refactoring"
tags:
  - 식탁보
  - 오픈소스
  - C#
  - 웹 개발
  - XSL
  - Generic Host
categories:
  - 개발
translationKey: "tablecloth-catalog-ui-refactoring"
description: "식탁보 카탈로그 페이지가 현대적인 카드 UI로 개편되고, 카테고리 필터 기능이 추가되었습니다. 또한 Generic Host 패턴 적용과 품질 관리 도구가 새롭게 도입되었습니다."
tldr: "100개 이상의 서비스 목록을 XSLT 기반 카드 UI + CSS Grid 반응형 레이아웃으로 전면 개편하고, 바닐라 JS 카테고리 필터와 Generic Host 패턴 리팩토링을 적용한 과정입니다."
cover:
  image: "images/posts/tablecloth-catalog-ui-refactoring.jpg"
  alt: "식탁보 카탈로그 UI 업데이트"
---

## 들어가며

한국에서 인터넷 뱅킹을 이용해본 적이 있다면, 각종 보안 프로그램 설치 요구에 고개를 끄덕이게 될 것입니다. ActiveX는 사라졌지만 그 자리를 대신한 수많은 보안 플러그인들—AhnLab Safe Transaction, TouchEn nxKey, Veraport 등—은 여전히 우리의 PC에 설치를 요구합니다.

[식탁보(TableCloth)](https://yourtablecloth.app) 프로젝트는 이런 보안 프로그램들을 Windows Sandbox라는 격리된 환경에서 실행할 수 있게 해주는 오픈소스 도구입니다. 그리고 [식탁보 카탈로그](https://github.com/yourtablecloth/TableClothCatalog)는 어떤 금융 사이트에서 어떤 보안 프로그램이 필요한지를 정리해둔 데이터베이스 역할을 합니다.

## 이번 업데이트 한눈에 보기

식탁보 카탈로그 프로젝트에 다섯 건의 커밋이 적용되었습니다. 이번 업데이트는 **프론트엔드**, **백엔드**, **DevOps** 세 영역에 걸친 종합적인 개선입니다.

| 영역 | 변경 사항 | 핵심 키워드 |
| ------ | ----------- | ------------- |
| **프론트엔드** | 카탈로그 웹 페이지 전면 재설계 | 카드 UI, 카테고리 필터, 반응형 레이아웃 |
| **백엔드** | 빌드 도구 아키텍처 리팩토링 | Generic Host, 의존성 주입, 구조화된 로깅 |
| **DevOps** | 품질 관리 자동화 도구 추가 | 이미지 검증, 미사용 리소스 정리, 파비콘 수집 개선 |

각 영역별로 무엇이 바뀌었고, 왜 그런 결정을 내렸는지 자세히 살펴보겠습니다.

---

## 프론트엔드: 테이블에서 카드로

### 왜 UI를 바꿔야 했을까?

기존 카탈로그 페이지는 전형적인 HTML 테이블 형태였습니다. 카테고리, 서비스 이름, 필요한 패키지 목록이 행과 열로 정렬된 구조였죠. 기능적으로는 문제가 없었지만, 몇 가지 한계가 있었습니다.

먼저, 100개가 넘는 서비스를 스크롤하며 찾아야 했습니다. 모바일 환경에서는 가로 스크롤이 발생해 사용성이 떨어졌고, 시각적 계층 구조가 없어 정보 파악이 어려웠습니다. 무엇보다 카테고리별 필터링이 불가능해서 원하는 서비스를 빠르게 찾기 어려웠습니다.

이런 문제를 해결하기 위해 카드 기반 UI로 전면 개편을 결정했습니다.

### XSL 트랜스폼으로 구현한 반응형 카드 UI

식탁보 카탈로그의 재미있는 점은 데이터가 XML 형식으로 저장되고, 웹 페이지는 **XSLT(XSL Transformations)**를 통해 렌더링된다는 것입니다. 별도의 서버 사이드 로직 없이 브라우저가 직접 XML을 HTML로 변환합니다.

#### 디자인 토큰 시스템 도입

현대적인 CSS 설계의 핵심은 **디자인 토큰**입니다. 색상, 간격, 그림자 등을 CSS 변수로 정의하면 일관성 있는 디자인을 유지하면서도 유지보수가 쉬워집니다.

```css
:root {
    /* 색상 팔레트 */
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    
    /* 그림자 */
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    
    /* 레이아웃 */
    --radius: 12px;
}
```

이 색상 체계는 Tailwind CSS의 기본 팔레트에서 영감을 받았습니다. 슬레이트 계열의 텍스트 색상과 블루 계열의 강조색을 조합하면 깔끔하면서도 전문적인 인상을 줄 수 있습니다.

### CSS Grid로 구현한 반응형 레이아웃

카드 레이아웃의 핵심은 CSS Grid의 `auto-fill`과 `minmax()` 조합입니다:

```css
.services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1.25rem;
}
```

이 한 줄의 CSS로 다음을 달성합니다. 화면 너비에 따라 열 개수가 자동으로 조절되고, 각 카드는 최소 340px를 유지하면서 가능한 공간에서 균등하게 분배됩니다. 카드 간 간격은 20px로 일관되게 유지됩니다.

340px라는 최소 너비는 모바일 환경(약 375px)에서도 단일 열로 깔끔하게 표시되도록 계산된 값입니다.

### 마이크로 인터랙션으로 생동감 부여

정적인 카드보다는 사용자 상호작용에 반응하는 카드가 더 매력적입니다:

```css
.service-card {
    transition: transform 0.2s, box-shadow 0.2s;
}

.service-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}
```

마우스를 올리면 카드가 살짝 떠오르는 효과입니다. 0.2초의 트랜지션 시간은 부드러우면서도 지연 없이 반응하는 느낌을 줍니다. 4px의 상승 거리는 미묘하지만 확실히 인지되는 수준입니다.

## JavaScript 카테고리 필터 구현

100개가 넘는 서비스 중에서 원하는 것을 찾으려면 필터링이 필수입니다. 간단한 바닐라 JavaScript로 구현했습니다:

```javascript
function filterCards(category) {
    const cards = document.querySelectorAll('.service-card');
    const buttons = document.querySelectorAll('.filter-btn');
    
    // 버튼 상태 업데이트
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // 카드 필터링
    cards.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}
```

핵심은 각 카드에 `data-category` 속성을 부여하는 것입니다. XSL에서 이렇게 생성합니다:

```xml
<div class="service-card" data-category="{@Category}">
```

이 방식의 장점은 몇 가지가 있습니다. 클라이언트에서 즉시 필터링하므로 서버 요청이 필요 없고, 단순 토글 기능이므로 복잡한 URL 상태 관리도 필요 없습니다. 또한 JavaScript가 비활성화된 환경에서도 모든 카드가 그대로 표시되어 점진적 향상(Progressive Enhancement) 원칙을 따릅니다.

### 카테고리별 시각적 구분

각 카테고리마다 고유한 색상 뱃지를 부여했습니다:

```css
.category-Banking { background: #dbeafe; color: #1e40af; }
.category-CreditCard { background: #fce7f3; color: #9d174d; }
.category-Government { background: #d1fae5; color: #065f46; }
.category-Financing { background: #fef3c7; color: #92400e; }
.category-Insurance { background: #e0e7ff; color: #3730a3; }
.category-Education { background: #f3e8ff; color: #6b21a8; }
.category-Security { background: #fee2e2; color: #991b1b; }
.category-Other { background: #f1f5f9; color: #475569; }
```

색상 선택에는 의미를 담았습니다. 은행(Banking)에는 신뢰와 안정을 상징하는 블루를, 카드(CreditCard)에는 결제와 연관된 핑크/마젠타를 적용했습니다. 공공기관(Government)에는 공공성을 나타내는 그린을, 금융(Financing)에는 돈을 연상시키는 앨버를 사용했습니다. 보험(Insurance)에는 보호를 의미하는 인디고를, 보안(Security)에는 주의와 경고를 나타내는 레드를 배정했습니다.

---

## 백엔드: Generic Host 패턴으로 리팩토링한 빌드 도구

UI 개선과 함께 백엔드 도구인 `catalogutil.cs`도 대폭 리팩토링되었습니다. 핵심은 .NET의 **Generic Host** 패턴 적용입니다.

### Generic Host란?

Generic Host는 .NET에서 애플리케이션의 수명 주기, 의존성 주입, 구성, 로깅 등을 관리하는 프레임워크입니다. 원래 ASP.NET Core 웹 애플리케이션에서 사용하던 패턴인데, .NET Core 3.0부터 콘솔 앱이나 백그라운드 서비스에서도 활용할 수 있게 되었습니다.

```csharp
// Generic Host 설정
var builder = Host.CreateApplicationBuilder(args);

// 구성에서 타임아웃 값 읽기
const double DefaultTimeoutSeconds = 15d;
const double MinTimeoutSeconds = 5d;
var configuredTimeout = builder.Configuration.GetValue("TimeoutSeconds", DefaultTimeoutSeconds);
var timeoutSeconds = Math.Max(configuredTimeout, MinTimeoutSeconds);

// 서비스 등록 (의존성 주입)
builder.Services.AddSingleton<CatalogLoader>();
builder.Services.AddSingleton<ImageConverter>();
```

### 왜 콘솔 앱에 Generic Host를?

"단순한 빌드 스크립트에 이런 복잡한 패턴이 필요한가?"라고 물을 수 있습니다. 하지만 Generic Host가 제공하는 이점은 분명합니다:

#### **의존성 주입(DI)**

```csharp
// 생성자 주입으로 의존성 명시
public class CatalogLoader
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<CatalogLoader> _logger;
    
    public CatalogLoader(HttpClient httpClient, ILogger<CatalogLoader> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }
}
```

DI를 사용하면 클래스 간 결합도가 낮아지고, 테스트가 쉬워지며, 의존성이 명시적으로 드러납니다.

#### **구성 관리**

```csharp
// appsettings.json 또는 환경 변수에서 설정 읽기
var timeout = builder.Configuration.GetValue("TimeoutSeconds", 15d);
```

하드코딩된 값 대신 외부 구성을 사용하면 환경별로 다른 설정을 적용할 수 있습니다.

#### **구조화된 로깅**

```csharp
_logger.LogInformation("Processing service: {ServiceName}", service.Name);
```

구조화된 로깅은 로그를 단순 문자열이 아닌 검색 가능한 데이터로 만들어줍니다.

---

## DevOps: 품질 관리 자동화와 파비콘 수집 개선

### 파비콘 수집 기능 개선

카탈로그의 각 서비스에 아이콘을 표시하려면 해당 웹사이트의 파비콘을 수집해야 합니다. 이번 업데이트에서 파비콘 수집 로직이 크게 개선되었습니다.

### 웹 앱 매니페스트 지원

현대 웹사이트들은 `manifest.json`(또는 `manifest.webmanifest`)을 통해 앱 아이콘을 정의합니다:

```json
{
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192" },
    { "src": "/icons/icon-512.png", "sizes": "512x512" }
  ]
}
```

새 버전에서는 HTML의 `<link rel="manifest">` 태그를 파싱하여 매니페스트 파일을 찾고, 그 안의 아이콘 정보를 추출합니다.

### 폴백 전략

하나의 방법으로 파비콘을 찾지 못하면 다음 방법을 시도합니다:

1. **웹 앱 매니페스트**: `manifest.json`의 icons 배열
2. **Link 태그**: `<link rel="icon">` 또는 `<link rel="shortcut icon">`
3. **기본 위치**: `/favicon.ico`
4. **외부 서비스**: Google Favicon 서비스 등 폴백

이런 다중 폴백 전략으로 대부분의 웹사이트에서 아이콘을 성공적으로 가져올 수 있습니다.

### 이미지 품질 관리 자동화

오픈소스 프로젝트에서 데이터 품질 관리는 항상 도전 과제입니다. 이번에 추가된 품질 관리 도구는 여러 검증 작업을 자동으로 수행합니다.

먼저 이미지 무결성 검증 기능이 있습니다. 카탈로그에 등록된 모든 서비스의 아이콘 파일이 실제로 존재하는지 확인하고, 손상되었거나 로드할 수 없는 이미지를 탐지합니다. PNG 포맷의 유효성도 함께 검사합니다.

다음으로 미사용 리소스 정리 기능이 있습니다.

```text
⚠️  Orphan image found: images/Banking/OldBank.png
    → This image is not referenced by any service in the catalog
```

서비스가 삭제되었지만 이미지는 남아있는 경우를 자동 탐지합니다.

---

## 마치며

이번 업데이트는 단순한 "예쁜 UI" 변경이 아닙니다. 사용자가 원하는 서비스를 빠르게 찾을 수 있도록 UX를 개선하고, 개발자가 프로젝트를 유지보수하기 쉽도록 코드 품질을 높이며, 데이터 무결성을 자동으로 검증하는 시스템을 구축했습니다.

오픈소스 프로젝트의 가치는 코드 한 줄 한 줄에 담긴 세심한 고민에서 나옵니다. 식탁보 프로젝트에 관심이 있으시다면, 직접 카탈로그 페이지를 방문해보시거나 GitHub에서 코드를 살펴보세요.

## 참고 링크

- [식탁보 카탈로그 GitHub](https://github.com/yourtablecloth/TableClothCatalog)
- [식탁보 프로젝트 홈페이지](https://yourtablecloth.app)
- [식탁보 카탈로그 웹 페이지](https://yourtablecloth.app/TableClothCatalog/)
- [.NET Generic Host 공식 문서](https://learn.microsoft.com/dotnet/core/extensions/generic-host)
