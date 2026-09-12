# 일일 재빌드를 통한 연재 예약 발행

- 결정일: 2026년 9월 13일
- 상태: 적용
- 대체 대상: [예약 발행 기능 철회](0001-retire-scheduled-publishing.md)

## 하루 간격의 다국어 연재 공개

Edge0 연재 5편을 한국어, 영어, 일본어로 하루 간격으로 공개합니다. 첫 공개 시각은 2026년 9월 13일 오전 9시(한국 시각)로 정하고 마지막 회차를 2026년 9월 17일에 공개합니다.

## 빌드 시각에 따른 콘텐츠 포함 여부

각 회차의 세 언어 파일에 같은 `date`와 `draft: false`를 지정합니다. 프로덕션 설정과 CI 명령은 `buildFuture=false`, `buildDrafts=false`를 유지합니다. Hugo는 미래 공개 날짜의 글을 빌드에서 제외하며 별도 `publishDate`가 있으면 해당 값을 공개 기준으로 사용합니다. [Hugo PublishDate 문서](https://gohugo.io/methods/page/publishdate/)

미공개 후속 편은 `series-link` shortcode에서 제목과 공개 예정 문구로 표시합니다. 대상 페이지가 해당 언어의 빌드에 포함되면 shortcode가 링크를 생성합니다. 공개 전후의 페이지, 목록, RSS, 검색 색인, 사이트맵과 내부 링크를 검증합니다. [Hugo shortcode 템플릿](https://gohugo.io/templates/shortcode/)

## 매일 오전 9시의 예약 실행과 복구

`deploy.yml`에 UTC 기준 `0 0 * * *`를 추가하고 기존 `main` 푸시 및 수동 실행을 유지합니다. 날짜마다 Git 파일을 수정하거나 자동 커밋을 만들지 않습니다. 전체 사이트를 다시 빌드하므로 실행을 건너뛴 뒤에도 다음 성공한 배포에서 기한이 지난 글을 모두 포함합니다.

GitHub는 기본 브랜치에서 예약 워크플로를 실행합니다. 대기열과 부하로 실행이 지연되거나 누락될 수 있으며 공개 저장소에 60일간 활동이 없으면 예약 실행을 비활성화할 수 있습니다. 따라서 오전 9시를 실행 요청 시각으로 사용하고 실제 공개 시각에는 빌드 및 배포 시간을 더합니다. 실행 실패 시 원인을 수정한 뒤 `main`의 같은 워크플로를 수동 실행합니다. [GitHub schedule 이벤트 문서](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## 공개 저장소와 운영 사이트의 구분

예약 시각 전에도 원고를 공개 Git 저장소에서 열람할 수 있습니다. 이 결정은 운영 사이트의 공개 순서를 제어하며 원고에 접근 제어를 추가하지 않습니다. 이전 결정에서 확인한 정확한 시각 보장과 사전 비공개 보관의 한계는 그대로 유지합니다. [이전 결정의 확인한 한계](0001-retire-scheduled-publishing.md#확인한-한계)
