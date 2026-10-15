# Page comments

Gerby uses GitHub Discussions for public comments. The site does not store a GitHub token or collect readers' email addresses. Readers sign into GitHub to post; existing discussions can be read publicly. The inline form is supplied by the hosted, open source [giscus service](https://giscus.app/).

## Repository setup

1. Enable Discussions on `MingchenXia/Gerby`.
2. Install the [giscus app](https://github.com/apps/giscus) with **Only select repositories**, selecting **Gerby**. Its discussion access is used to create and update comment threads.
3. Keep the public repository ID and General category ID in `comments.json` in sync with GitHub. These IDs are not credentials.
4. Keep `giscus.json` at the repository root. It permits the deployed homepage origin and local preview origins.
5. Open a reading page's Comments section and confirm that the embedded sign-in/comment form appears. Merely enabling GitHub Discussions is not enough to activate the inline form.

The page always offers direct GitHub discussion links. A service failure shows an explanatory message and a retry button instead of silently hiding comments.

## Stable threads

Each thread is identified by `Gerby /<route>/`, using a canonical entry tag, chapter slug, or section slug. It is independent of page title and source revision. Old source URLs redirect to the canonical entry and therefore share that entry's comments.

giscus uses strict matching with the SHA-1 marker of the thread identifier. The direct GitHub composition link includes the same marker and a link to the reading page, so a thread created through the fallback can later appear inline. Keep this hidden marker when editing a thread's original post.

Threads are created when a reader first comments. A build or page view does not pre-create thousands of empty discussions. Development checks must not post test comments to the public repository.

## Moderation

Moderate, edit, lock, or remove comments through the repository's Discussions interface. Use the page link and identifier to locate the relevant mathematical statement. Replies, reactions, and moderation persist separately from site deployments. The comment service loads only as the reader approaches the Comments panel or asks to load it.

Comment counts are displayed only when returned by the service; an unavailable thread is not reported as having zero comments. The embed accepts messages only from its own giscus iframe and the documented giscus origin.
