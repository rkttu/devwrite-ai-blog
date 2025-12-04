---
title: "Windows 10/11 Pro에서 Hyper-V 2세대 VM으로 Ubuntu 부팅하기"
date: 2025-10-23T00:00:00+09:00
draft: false
slug: "using-ubuntu-with-hyperv-gen2"
tags:
  - Hyper-V
  - Ubuntu
  - 가상화
  - Windows
categories:
  - 개발 환경
translationKey: "using-ubuntu-with-hyperv-gen2"
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "서버 가상화 환경 이미지"
tldr: "Hyper-V 2세대 VM에서 Ubuntu가 부팅되지 않는다면, 보안 부팅 템플릿을 'Microsoft UEFI 인증 기관'으로 변경하세요."
---

## 시작하기

Windows Pro에는 기본적으로 Hyper-V가 포함되어 있습니다. 별도의 가상화 소프트웨어를 설치하지 않아도, 운영체제 안에서 바로 가상 머신을 만들고 관리하실 수 있습니다. 이번 글에서는 Hyper-V의 2세대(Generation 2) 가상 머신을 이용해 Ubuntu를 부팅하는 방법을 정리해보겠습니다.

먼저 관리자 권한 PowerShell을 열고 다음 명령어를 입력해 Hyper-V 기능을 활성화합니다.

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

설치가 완료되면 재부팅해주십시오.

그 다음 “Hyper-V 관리자”를 실행해 새 가상 머신을 생성합니다. 세대는 반드시 2세대(Generation 2) 로 선택하고, 메모리는 4GB 이상, 디스크는 20GB 이상으로 지정하시면 됩니다.

네트워크 어댑터는 “기본 가상 스위치(Default Switch)”를 선택하시면 별도의 설정 없이 바로 인터넷 연결이 가능합니다.

이제 [Ubuntu 공식 사이트](https://ubuntu.com/download/desktop)에서 ISO 이미지를 내려받으신 뒤, 가상 머신의 DVD 드라이브 → 이미지 파일 사용 항목에 연결합니다.
그리고 펌웨어(Firmware) 설정에서 DVD 드라이브를 부팅 순서의 가장 위로 올려두시면 ISO로부터 바로 부팅할 수 있습니다.

## 중요한 부분

여기까지는 일반적인 절차입니다. 하지만 실제로 Ubuntu를 설치하려 하면 “No bootable device”나 “Start boot option” 같은 오류가 발생해 부팅이 되지 않는 경우가 많습니다.

**그 이유는 간단합니다. Hyper-V의 2세대 VM은 기본적으로 Windows 전용 UEFI 보안 부팅 템플릿을 사용하기 때문입니다.**

이 문제를 해결하려면, 가상 머신을 만든 뒤 반드시 “설정 → 보안(Security)” 항목으로 이동하셔야 합니다.

여기서 **‘보안 부팅 사용(Enable Secure Boot)’**을 체크하시고, 아래쪽의 ‘템플릿(Template)’ 옵션을 “Microsoft UEFI 인증 기관(Microsoft UEFI Certificate Authority)” 으로 변경해주십시오.
이 설정이 올바르게 되어 있지 않으면, Ubuntu의 부트로더가 서명되지 않은 이미지로 인식되어 UEFI에서 부팅을 차단하게 됩니다.
즉, ISO 파일이나 디스크 구성을 아무리 다시 만들어도 이 설정이 빠져 있으면 Ubuntu는 절대 부팅되지 않습니다.

위 단계를 마치면 Ubuntu 설치 화면이 정상적으로 표시되며, 안내에 따라 설치를 진행하실 수 있습니다.

Ubuntu 20.04 이상 버전은 Hyper-V 통합 서비스가 기본 포함되어 있어서, 별도의 드라이버 설치 없이도 클립보드 공유, 화면 해상도 자동 조정, 시간 동기화 같은 기능이 바로 작동합니다.

결론적으로, Hyper-V 2세대 VM에서 Ubuntu를 부팅하려면 ‘보안 부팅 템플릿’을 반드시 Microsoft UEFI 인증 기관으로 지정해야 합니다.

이 한 가지 설정만 잊지 않으신다면, Windows Pro 환경에서도 안정적으로 Ubuntu를 실행하고 개발 환경을 구축하실 수 있습니다.
