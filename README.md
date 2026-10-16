Dieses Ressource Pack wird nicht mehr weitergearbeitet.\
Die Weiterentwicklung geschieht in [https://github.com/EnderNationTeam/minecraft-resource-pack](https://github.com/EnderNationTeam/minecraft-resource-pack)


# EnderNation Resource Pack

Technische Projektdoku für das aktuelle Pack-Setup.

## Status

- Zielversion: **Minecraft Java 26.3** (bestehender 1.21.11+-Modellaufbau)
- Das alte System mit **einzelnen Vanilla-Basisitems pro Waffe** wurde wiederhergestellt
- Aktive Java-Itemdefinitionen liegen in `assets/minecraft/items/`
- Bedrock-/Geyser-Struktur liegt zusätzlich in `bedrock/` und `geysermc/`
- Alte Test-/Legacy-Dateien wurden in `archive/` gesichert

## Projektstruktur

- `assets/enderguns/` → Modelle, Texturen und eigene Inhalte
- `assets/minecraft/items/` → aktive Java-Itemdefinitionen für 1.21.11
- `assets/minecraft/models/item/` → saubere Vanilla-Basisdateien
- `bedrock/` → Bedrock-Resource-Pack für Geyser/Bedrock-Clients
- `geysermc/` → Geyser-Mappings + CMD-Registry
- `archive/` → alte Experimente, Testdateien und Legacy-Zustände
- `dist/` → gebaute Test-Artefakte
- `scripts/restore-legacy-base-items.ps1` → stellt die alte Basisitem-Verteilung wieder her

## Fertige Test-Dateien

Nach dem Build liegen fertige Dateien in `dist/`:

- `EnderNation-Resource-Pack-Java-1.21.11.zip`
- `EnderNation-Resource-Pack-Bedrock-1.21.11.mcpack`
- `EnderNation-Geyser-Config-1.21.11.zip`

## Neu bauen

```powershell
& "C:\Users\marce\IdeaProjects\EnderNation-Resource-Pack\build-packs.ps1"
```

## Give-Syntax in 1.21.11

Das aktive System arbeitet jetzt wieder mit:

- **einem einzelnen Vanilla-Basisitem pro Waffe**
- plus **`custom_model_data`**

Wichtig: In `1.21.11` ist `custom_model_data` **eine Struktur**, nicht nur eine nackte Zahl.

Schema:

```mcfunction
/give @p <basisitem>[custom_model_data={floats:[<id>.0]}] 1
```

Für fast alle Waffen ist die ID jetzt wieder `1`.

## Aktive IDs / Zuordnung

Quelle: `geysermc/cmd_registry.json`

### Waffen

| Basisitem | ID | Name |
|---|---:|---|
| `diamond_pickaxe` | `1` | `aa_12` |
| `iron_hoe` | `1` | `ak_47` |
| `wooden_axe` | `1` | `cz_550` |
| `diamond_shovel` | `1` | `desert_eagle` |
| `golden_hoe` | `1` | `fal` |
| `golden_shovel` | `1` | `five_seven` |
| `stone_shovel` | `1` | `g17` |
| `wooden_pickaxe` | `1` | `m1014` |
| `diamond_hoe` | `1` | `m16` |
| `iron_shovel` | `1` | `m1911` |
| `iron_axe` | `1` | `m39` |
| `wooden_shovel` | `1` | `m9` |
| `diamond_axe` | `1` | `m98b` |
| `wooden_hoe` | `1` | `mp7` |
| `golden_axe` | `1` | `msr` |
| `stone_hoe` | `1` | `p90` |
| `stone_pickaxe` | `1` | `remington_870` |
| `blaze_rod` | `1` | `rocket_launcher` |
| `iron_pickaxe` | `1` | `spas_12` |
| `golden_pickaxe` | `1` | `striker` |
| `stone_axe` | `1` | `sv98` |

### Utilities

| Basisitem | ID | Name |
|---|---:|---|
| `paper` | `1` | `bandage` |
| `paper` | `2` | `advanced_medikit` |
| `glowstone_dust` | `1` | `flashbang` |
| `slime_ball` | `1` | `grenade` |

### Ammo

| Basisitem | ID | Name |
|---|---:|---|
| `snowball` | `1` | `bullet` |
| `gold_nugget` | `1` | `pistol_ammo` |
| `flint` | `1` | `rifle_ammo` |
| `wheat_seeds` | `1` | `shotgun_ammo` |
| `clay_ball` | `1` | `sniper_ammo` |
| `ghast_tear` | `1` | `rocket_launcher_ammo` |

## Schnelle Beispiele

### AA-12

```mcfunction
/give @p diamond_pickaxe[custom_model_data={floats:[1.0]},custom_name='{"text":"AA-12","italic":false}'] 1
```

### AK-47

```mcfunction
/give @p iron_hoe[custom_model_data={floats:[1.0]},custom_name='{"text":"AK-47","italic":false}'] 1
```

### Desert Eagle

```mcfunction
/give @p diamond_shovel[custom_model_data={floats:[1.0]},custom_name='{"text":"Desert Eagle","italic":false}'] 1
```

### Advanced Medikit

```mcfunction
/give @p paper[custom_model_data={floats:[2.0]},custom_name='{"text":"Advanced Medikit","italic":false}'] 1
```

### Flashbang

```mcfunction
/give @p glowstone_dust[custom_model_data={floats:[1.0]},custom_name='{"text":"Flashbang","italic":false}'] 1
```

### Bullet

```mcfunction
/give @p snowball[custom_model_data={floats:[1.0]},custom_name='{"text":"Bullet","italic":false}'] 1
```

## Hinweise

- Java lädt das gebaute ZIP direkt aus `dist/`
- Bedrock nutzt das `.mcpack` aus `dist/`
- Geyser benötigt zusätzlich die Dateien aus `geysermc/` bzw. aus `EnderNation-Geyser-Config-1.21.11.zip`
- Die bestehenden Unicode-/Font-Glyphen in `assets/minecraft/font/default.json` wurden nicht geändert

## Bedrock-Kandidat 26.3 / ai-dev

Die neue Bedrock-Konvertierung mit echten 3D-Modellen, getrennten Handansichten und Geyser-v2-Mappings ist in [docs/BEDROCK-26.3.md](docs/BEDROCK-26.3.md) beschrieben. Servertests und nativer Geyser-Import sind bestanden; echte Client-Abnahme und produktive Pack-Installation stehen aus.
