# Prompt: Unpublish Post

## Task

Change a published post's status from `draft: false` to `draft: true` to unpublish it.

## Input

- **Post slug**: 게시 취소할 포스트의 슬러그

## Use Cases

- 내용에 오류가 발견되어 수정이 필요한 경우
- 임시로 게시를 중단해야 하는 경우
- 시기적으로 부적절한 내용이 있는 경우

## Actions

### 1. Update All Language Versions

모든 언어 버전의 `draft` 값을 변경:

```yaml
# Before
draft: false

# After
draft: true
```

### Files to Update

- `content/ko/posts/{slug}.md`
- `content/en/posts/{slug}.md`
- `content/ja/posts/{slug}.md`

### 2. Verify Unpublication

Hugo 서버가 실행 중이면 자동으로 반영됩니다.
해당 URL 접속 시 404가 표시됩니다 (draft 포스트는 기본적으로 숨김).

**Draft 포함 빌드**: `hugo server --buildDrafts`

## Output

```
## 게시 취소 완료: {slug}

### 변경된 파일
- ✅ content/ko/posts/{slug}.md (draft: true)
- ✅ content/en/posts/{slug}.md (draft: true)
- ✅ content/ja/posts/{slug}.md (draft: true)

### 상태
포스트가 draft 상태로 변경되어 사이트에서 숨겨집니다.
Draft를 포함하여 미리보기: hugo server --buildDrafts
```

## Re-publish

다시 발행하려면 `/publish-draft` 프롬프트를 사용하세요.
