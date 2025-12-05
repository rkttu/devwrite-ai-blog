---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ .Date }}
draft: true
slug: "{{ .File.ContentBaseName }}"
tags: []
categories: []
translationKey: "{{ .File.ContentBaseName }}"
cover:
  image: ""
  alt: ""
tldr: ""
# license: "CC BY-NC 4.0"  # 기본값 사용 시 생략 가능. 변경 시: CC BY 4.0, CC BY-SA 4.0, MIT, All Rights Reserved 등
---
