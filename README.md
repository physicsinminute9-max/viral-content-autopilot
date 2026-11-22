# Viral Content Autopilot (starter)

This repository creates one original 1080x1350 quote/design image per scheduled run and can publish it to a Facebook Page and a Pinterest board.

## Important limitations

- This starter makes designed graphics with Python/Pillow. It does **not** generate photorealistic AI images or live-trending content. It uses an editable set of original sample captions and designs.
- GitHub Actions is a CI runner, not an always-on server. Free minutes and fair-use limits apply. Check your GitHub billing page.
- Social platform API access, app review, scopes, and account eligibility are controlled by Meta and Pinterest. API access is not guaranteed just because an account is a Page admin or Business account.
- Pinterest image upload uses the `image_base64` media source. If Pinterest rejects this media source for your app/version, use the official image URL method and a public image host.
- Do not commit access tokens or passwords. Add them only as GitHub Actions secrets.

## Files

- `main.py` - creates a graphic and publishes to both platforms.
- `requirements.txt` - Python dependencies.
- `.github/workflows/publish.yml` - 5 daily UTC schedules and manual preview.

## Add GitHub Actions secrets

Repository -> Settings -> Secrets and variables -> Actions -> New repository secret:

1. `FB_PAGE_ID`
2. `FB_PAGE_ACCESS_TOKEN`
3. `PINTEREST_ACCESS_TOKEN`
4. `PINTEREST_BOARD_ID`

Optional repository variable:
- `BRAND_NAME` (for example your Page name)

### Meta / Facebook

Create a Meta developer app and obtain a **Page access token** for the Page. Required permissions for Page photo publishing include `pages_manage_posts`, `pages_read_engagement`, and `pages_show_list`. The token must belong to a person with the Page's content-creation task. See:
https://developers.facebook.com/docs/graph-api/reference/page/photos/

### Pinterest

Create/connect a Pinterest developer app and obtain an OAuth access token with `boards:read`, `pins:read`, and `pins:write`. Find the ID of the destination board using the Pinterest API's list boards endpoint or developer tools. See:
https://developers.pinterest.com/docs/work-with-organic-content-and-users/create-boards-and-pins/

## First test (do not publish)

1. Open the repository's Actions tab.
2. Choose `Viral Content Autopilot`.
3. Click `Run workflow`.
4. Keep `publish` set to `false`.
5. Run it and download the generated image from the run's Artifacts section.

## Enable publishing

After adding and verifying all four secrets:
1. Run workflow manually with `publish=true` for a single test post.
2. Confirm it appears correctly on both accounts.
3. Scheduled runs then publish at 08:00, 11:00, 14:00, 17:00 and 20:00 Sri Lanka time.

GitHub cron times are UTC. These times are UTC+05:30.

## Edit content/design

Edit the `POSTS` list in `main.py`. Change `BRAND_NAME` in repository variables.
