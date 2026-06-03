# Wiki source (EN / IT)

Bilingual GitHub Wiki pages. Each page has an English section and an Italian section with cross-links at the top.

## Publish to the GitHub Wiki

The wiki is a separate git repo (`<repo>.wiki.git`). Initialize it once via the
repo's **Wiki** tab (create the first page), then push these files:

```powershell
git clone https://github.com/<user>/FNIRSI-IPS3608.wiki.git
Copy-Item wiki\*.md FNIRSI-IPS3608.wiki\ -Force
cd FNIRSI-IPS3608.wiki
git add .
git commit -m "Add bilingual EN/IT wiki"
git push
```

GitHub maps file names to page titles, so `GUI-Usage.md` → **GUI Usage**.
`_Sidebar.md` and `_Footer.md` render on every page.

## Pages

- `Home.md`, `Installation.md`, `GUI-Usage.md`, `CLI-and-Scripting.md`,
  `Memory-Presets.md`, `Routines.md`, `Protocol-Reference.md`,
  `Architecture.md`, `Contributing.md`
- Navigation: `_Sidebar.md`, `_Footer.md`
