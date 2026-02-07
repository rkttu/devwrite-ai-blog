---
title: "/dev/write: Running a Tech Blog with AI"
date: 2025-12-05T10:00:00+09:00
draft: false
slug: "introducing-devwrite-blog"
tags:
  - blog
  - Hugo
  - static site
  - multilingual
categories:
  - Guide
translationKey: "introducing-devwrite-blog"
description: "A multilingual tech blog built with GitHub Copilot and Hugo. Supports AI-powered writing, automatic translation, and scheduled publishing."
tldr: "A multilingual tech blog built with GitHub Copilot and Hugo. Supports AI-powered writing, automatic translation, and scheduled publishing."
cover:
  image: "images/posts/introducing-devwrite-blog.jpg"
  alt: "Laptop and coffee for blog writing"
---

The biggest challenge in running a tech blog is "how do I consistently write quality content?" Add multilingual support to the mix, and the workload doubles with translations.

/dev/write was born from these struggles. By combining Hugo static site generator with GitHub Copilot, I built an environment where **you can focus solely on writing**.

## Why Another Blog System?

Honestly, existing blog platforms are great. Medium, Dev.to, Hashnode—all excellent choices. But there were a few pain points.

First, **multilingual support**. I wanted to publish posts in Korean, English, and Japanese, but most platforms required separate accounts or complex configurations.

Second, **concerns about AI training data**. Having my carefully written content used for AI model training without consent isn't exactly pleasant.

Third, **automated workflows**. I wanted to automate the process of writing, reviewing, translating, and publishing as much as possible.

So I built a system based on Hugo + PaperMod theme that addresses all three.

## Writing with GitHub Copilot

The most interesting part of /dev/write is using GitHub Copilot as a writing tool. In VS Code, you can invoke various prompts with the `/` command.

```text
/create-draft Write about Docker container networking
```

You can just throw a topic like this, or provide a more detailed outline.

```text
/create-draft
- Topic: Kubernetes Introduction
- Cover: Pod, Service, Deployment concepts
- Target: Developers familiar with Docker
```

If you have an existing README or documentation, you can ask it to create a tutorial based on that.

```text
/create-draft Create a tutorial post based on this README
#file:README.md
```

### AI Doesn't Write Everything

Of course, leaving everything to AI from start to finish isn't always the answer. In fact, **writing the draft yourself first and having AI flesh it out** often produces better results.

For example, if you want to migrate a post from your old blog and rewrite it in a tech blog style:

```text
/complete-manual-post Rewrite this post in a tech blog style
#file:my-old-post.md
```

If you have a draft you wrote yourself, you can ask for code examples or more detailed explanations.

```text
Based on this draft I wrote, make the content richer.
Add code examples and more detailed explanations.
#file:2025-12-05-my-draft.md
```

For posts where personal experience or opinions matter, or when you want to verify technical accuracy yourself, this approach is much more effective. AI is just a helper—the final judgment is yours.

## Write One, Get Three

Another feature of /dev/write is **automatic translation**. Write in Korean, and English and Japanese versions are automatically generated.

Sure, machine translation has its limits. But it's far better than writing in three languages from scratch. Just review the results and fix what needs fixing.

To maintain consistency during translation, there are a few rules:

- Metadata like `slug`, `translationKey`, `date` stays identical across all languages
- Title, tags, summary, and body content are translated
- Code blocks are not translated (obviously!)

English uses American English, Japanese uses です/ます form. Technical terms are kept in the original language or shown in parentheses.

After translation, a validation script checks that all three language versions are properly aligned.

```powershell
.\scripts\validate-translations.ps1
```

### Verifying Technical Accuracy

The most important thing in a tech blog is **accuracy**. Especially when covering Microsoft technologies like Azure or .NET, checking against official documentation is essential.

/dev/write automates this through the **MS Learn MCP Server**. The MCP server is registered in the `mcp.json` file and configured for use.

The MCP server queries Microsoft's official documentation to check if you're using the latest API versions, if any features are deprecated, and if your content aligns with official recommendations. It helps prevent those "this method is no longer recommended" comments on your blog posts.

## Scheduled Publishing with Social Media in Mind

Once you've written your post, it's time to publish. /dev/write supports **scheduled publishing**. Set a future date in the `date` field, and it automatically publishes at that time.

```yaml
date: 2025-12-10T08:00:00+09:00  # Publishes on Dec 10 at 8 AM
```

Scheduled publishing works via GitHub Actions cron triggers. Running it all day would waste runner costs, so I configured it to run **three times daily, aligned with social media peak times**.

- **8:00 AM**: When people check their phones during the commute
- **12:00 PM**: Quick browsing during lunch break
- **5:00 PM**: Last feed check before leaving work

```yaml
schedule:
  - cron: '0 23 * * *'  # KST 08:00
  - cron: '0 3 * * *'   # KST 12:00
  - cron: '0 8 * * *'   # KST 17:00
```

If you need a more precise publishing schedule, you can set up triggers locally. Using Windows Task Scheduler or crontab, you can adjust to hourly, every 30 minutes, or whatever interval you want. Save on GitHub Actions free tier usage while getting more precise publishing timing.

## Blocking AI Crawlers

These days, AI training crawlers scraping websites is a hot topic. /dev/write includes settings to block major AI crawlers by default.

GPTBot, Google-Extended, CCBot, anthropic-ai, and most other AI training crawlers are blocked via `robots.txt`, with meta tags as a second layer of defense. Sure, malicious crawlers can ignore this, but at least you've officially stated "please don't use my content for AI training."

## Local Preview

Want to see how your post looks before publishing? Just run the Hugo server locally.

```powershell
hugo server -D
```

The `-D` flag shows posts with `draft: true`. Access `http://localhost:1313` in your browser for a live preview. Files auto-refresh when you make changes, so it's easy to check your work.

## Wrapping Up

/dev/write isn't perfect yet. But I think it's achieved the goal of **focusing on writing and automating the rest**.

Multilingual support, AI-assisted editing, scheduled publishing, crawler blocking—the basics for running a tech blog are in place. I'll keep improving it.

If you're interested, check out the [GitHub repository](https://github.com/rkttu/devwrite-ai-blog). Feedback is always welcome! 🚀
