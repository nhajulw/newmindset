# គំនិតថ្មី · New Mindset — blog

The article behind every New Mindset Short. Posts are written by the studio (`scripts/blog-article.py`) and added by
`scripts/blog-publish.py`; `build.py` turns `posts/` into the site, and GitHub Actions publishes it to GitHub Pages
on every push and every 15 minutes (so scheduled posts appear on time).

Preview locally: `python3 build.py && python3 -m http.server 8090 --directory _site`
