# PF BETA 0.1.1: missing glyphs in body text and annotations

PF BETA 0.1 included the correct Chinese strings for Rain Dancers, but its
PhotonR2 font subset omitted characters used by the final reviewed text.
At record `photonflowers11.rio:488271272`, order 98 uses `伶` in the annotation
`首席女伶`, and order 103 uses `亟` in `国土亟待收复`. Windows GDI returned missing
glyphs for both. This was a font coverage omission, separate from the PM
[special-text directive issue](pm-special-text-20260911.md).

The audit covered the current 13,025 PF entries and 44,698 PM entries, including
Chinese annotations. PF needed 11 absent characters: **亟伶抉捆涟淀漪箍绎菊诘**.
PM had no missing characters within this scope. It does not establish that all
other UI surfaces, images, runtime font choices, or complete routes are fault-free.

## Repair

The existing `localization.tools.extend_font_subset` appends the 11 glyphs from
the locked OFL Noto Sans SC donor at weight 400. The 4,715 original glyphs,
outlines, metrics, character mappings, and shaping tables are preserved; the
new font contains 4,726 glyphs. The family remains PhotonR2.
`rUGP.tools.runtime.rebind_photon_font` changes only the 64-byte font digest in
the existing DLL. The font guard stays enabled, and font and DLL must ship together.

| Input/output | SHA-256 |
| --- | --- |
| Public PF BETA 0.1 ZIP | `E8933FAB8D3E4285A82269653B3F58D738BA6B2803BC2C96B956D5D148EFCCC3` |
| Original font | `AADF895003AE6452E1FBDCA1B64206B77D6F9A6EEBE226C31D46D1247AD4830B` |
| OFL donor | `763146584CF0710223441356B4395E279021B0806C196614377A7A0174AE074A` |
| Fixed font | `938A0046459DECF03FC11DC4D7FB9D440287EBE162C2F55F5964FAE661B0EC64` |
| Original runtime | `80F311F3AC8FAEA4612C779CAF718E238FE0ACAADB8CB739A4917D8C44AFB684` |
| Fixed runtime | `E7F3B5D1D3E6B63CBD2E69CA408C820FBBE5644DE4A371B49626F6EF1A06A9EC` |

The complete PF package preserves all BETA 0.1 text, image, animation, and
backlog-button payloads. Only the font, its companion DLL, manifest, and manifest
seal change inside the installer. The manifest explicitly accepts the public
BETA 0.1 fixed files for direct upgrades; backups remain disabled.

## Reproduce

Run from the repository root with the exact old public ZIP and licensed donor:

```powershell
python -m rUGP.packaging.build_pf_beta011 --old-zip "X:/inputs/MuvLuv_PF_CN_Patch_BETA_0.1.zip" --donor "X:/fonts/NotoSansSC-VF.ttf" --output "X:/build/pf-beta011" --csc "C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe"
```

The builder rejects different inputs and unexpected package changes, pins both
new output identities, and compares independently embedded payloads. Generated
game content and font binaries stay outside Git. The existing font license
notices remain bundled. Internal build: `2026.09.14-r4`.

## Validation scope

The fixed font covers every required PF body/annotation codepoint. Windows GDI
at 12, 24, and 36 pixels renders all 11 additions; representative existing
body/annotation dimensions are unchanged. In-game checks confirmed `首席女伶`,
`亟待收复`, and `积淀`. New empty-slot saves were made at the three exact lines;
reloading the annotation save restored its expected line. The maintainer
accepted the repair. No claim of exhaustive route testing is made.
