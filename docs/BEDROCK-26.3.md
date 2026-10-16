# Bedrock-Kompatibilität: Entwicklungskandidat 16.10.2026

**Nach ausdrücklicher Freigabe installiert; visuelle Abnahme läuft.** Der Proxy wurde einmal neu gestartet. Reine Pack-Korrekturen werden bei unveränderten Mappings über Geysers dokumentierten Reload geladen; sämtliche Minecraft-Java-Prozesse bleiben dabei unverändert. Das native Geyser-Prüfprogramm bestätigt keine identische Kamera-/Handdarstellung.

## Grundlage

Das aktuell ausgelieferte Java-Pack verweist auf dieses Repository und den Release-Tag `update-26.3`. Grundlage der neuen `ai-dev`-Arbeiten ist `76585cb` (inklusive halbierter Sounds und bestehender Mülltonne). Das ältere Repository `EnderNationTeam/minecraft-resource-pack`, Stand `e1b0ab9`, diente als 3D-/Animationsreferenz; es wurde nicht mit alten Java-Dateien über den aktuellen Stand kopiert.

Die vorherige aktive Bedrock-Fassung verwendete für die Waffen eine gemeinsame flache Ersatzgeometrie. Die ältere 3D-Fassung enthielt veraltete Haltewerte. Jetzt werden Geometrien, Drehpunkte, Texturen, UVs und vollständige XYZ-Ansichten aus den aktuellen Java-Modellen erzeugt. Für jeden Kontext gibt es eigene Haupt-/Nebenhand-Ansichten sowie Kopfansicht und Ausblenden am eigenen Kopf. Insbesondere wird die X-Drehung der Third-Person-Ansicht nicht mehr verworfen.

## Inhalt

- 32 Modelle: 21 Waffen sowie Munition, Projektil, Hilfsitems und Mülltonne. Jede echte Java-Kuboid-Geometrie bleibt als echte Bedrock-Kuboid-Geometrie erhalten. Flache Vanilla-Hilfsitems werden anhand ihrer tatsächlichen transparenten Texturen extrudiert.
- 62 eindeutige Geyser-v2-Definitionen für vorhandene Custom-Model-Data- und `item_model`-Varianten. Die 31 bisherigen `geyser_custom:eg_*`-IDs bleiben kompatibel; zusätzliche Modellvarianten erhalten eigene IDs. Das Projektil besitzt ausschließlich die tatsächlich vorhandene CMD-Variante.
- Eigene Inventarsymbole aus den Java-GUI-Ansichten, anstatt den Textur-Atlas als Inventarsymbol zu zeigen.
- Alle 32 enthaltenen Sounddateien einschließlich Lautstärke 0,5 sowie 73 private Unicode-Glyphen aus dem aktuellen Java-Pack.
- Bestehende Pack-UUIDs bleiben erhalten; die Pack-Version steigt von `[1,21,11]` über die geprüften Zwischenstände auf `[1,21,15]`, damit Clients den neuen Stand laden.
- Einzige Java-Änderung: `assets/enderguns/models/ammo/rocket_launcher_ammo.json` verwies auf eine nicht vorhandene Vanilla-Textur. Die Referenz zeigt nun auf die vorhandene EnderGuns-Textur. Alle anderen Java-Dateien wurden gegen den gesicherten Ausgangsstand geprüft und bleiben unverändert.

Die Referenz `docs/bedrock-source-lock.json` enthält den Java-Ausgangscommit und die ursprünglichen Datei-Prüfsummen. Der vollständige Erzeugungscode ist versioniert; zukünftige Java-Modelländerungen können erneut konvertiert werden. Nicht unterstützte UV-Rotationen oder Element-Rescale werden ausdrücklich abgewiesen statt stillschweigend falsch umgesetzt.

## Bauen und prüfen

```text
python -m pip install -r requirements-bedrock.txt
python scripts/build-bedrock-compat.py
```

Die Builds schreiben nur neue/erzeugte Bedrock-Ressourcen und `geysermc/geyser_mappings.json`; sie installieren nichts auf einem Server. Die bisherige `build-packs.ps1` und die Java-Release-Workflows bleiben erhalten. Auf dem PC nur bauen; Funktionstests entsprechend dem Projektauftrag auf dem Server ausführen:

```text
python tests/test_bedrock_compat.py
python scripts/validate-and-build-java-pack.py
```

Ausgabe unter `dist/bedrock-compat-20261016/`:

- `EnderNation-Bedrock-26.3.mcpack`
- `EnderNation-Geyser-Mappings-26.3.zip`
- `build-report.json` mit Quellen, Hashes und Modellübersicht
- `item-preview.png` als technische GUI-Vorschau; kein Minecraft-Screenshot

Der vorhandene Java-Builder erzeugt zusätzlich `dist/EnderNation-Resource-Pack.zip` samt Prüfsummen. Es wurde kein GitHub-Release veröffentlicht und kein produktiver Download-Tag verschoben. `ai-dev` löst die bestehenden Veröffentlichungsworkflows nicht aus.

## Servernachweise

18 Ressourcen-Vertragstests auf dem Proxmox-Server bestanden. Der vorhandene Java-Validator prüfte 109 JSON-Dateien, 427 PNG-Dateien, 58 Font-Provider, 32 Soundreferenzen und 109 Modellverweise erfolgreich und baute ein gültiges Java-ZIP mit 676 Dateien.

Zusätzlich wurde die offizielle Geyser-Standalone-Version **2.11.3-b1249**, exakt wie am Proxy, mit geprüftem Download-Hash gestartet. Die Testinstanz lauschte ausschließlich auf `127.0.0.1:39132` (IPv4-gemappter IPv6-Socket) und wurde anschließend beendet. Ein Kontrolllauf ohne eigene Mappings registrierte ein internes Item; mit diesen Mappings waren es 63, also **62 vollständig registrierte EnderNation-Definitionen**. Keine Mapping-/Pack-Ladefehler. Das Debugprotokoll enthält einen optionalen Netty-Hinweis `sun.misc.Unsafe unavailable`; Geyser initialisierte dennoch vollständig und verwendete seinen Fallback. Dieser Hinweis bleibt im Nachweis erhalten.

Nachweise: `docs/evidence-bedrock-20261016/`. Tests nutzten keine produktiven Welten oder Minecraft-Dienste.

## Installation nach gesonderter Freigabe

Nur der Proxy braucht das neue Pack. Im aktuellen Proxy und seiner CloudNet-Vorlage die bisherigen Dateien zuerst sichern. Danach das neue `.mcpack` nach `plugins/Geyser-Velocity/packs/` legen und die ersetzte alte Pack-Version aus diesem aktiven Verzeichnis herausnehmen. Genau `geyser_mappings.json` nach `custom_mappings/` übernehmen; `cmd_registry.json` ist Quellmetadaten und wird nicht als Mapping geladen. Alte Dateien bleiben im Backup wiederherstellbar.

Die vorhandene Geyser-Konfiguration für Custom Content und erzwungene Resourcepacks bleibt bestehen. Floodgate-Schlüssel und Firewall werden nicht verändert. Ein notwendiger Proxy-Neustart braucht ausdrücklich eine neue Freigabe; die vorherige Freigabe wurde für Vulcan/Floodgate verbraucht.

Der öffentliche UDP-Port 19132 wurde auf ausdrücklichen Nutzerauftrag dem vorhandenen OPNsense-Alias `endernation_cloudnet` hinzugefügt. Öffentlicher Bedrock-Beitritt ist inzwischen im echten Client bestätigt.

## Verbindliche Client-Abnahme

Mit Java und Bedrock alle Waffen vergleichen: First-/Third-Person, Haupt-/Nebenhand und linke dominante Hand, Schießen, Nachladen, Zoom, Verzauberungsglanz und Projektiltextur. Die genaue Kamera-/Handbasis und enginebedingte Unterschiede sind erst damit bestätigt. Die Datenkonvertierung beweist keine Pixelgleichheit.

Bedrocks private Font-Zellen können die sehr breiten Java-Schilder/Logos nicht zwangsläufig in identischer Breite und Höhe darstellen. Die Glyphen sind enthalten; die Lesbarkeit muss im Client geprüft werden. Inventar-/Boden-Itemdarstellung und Display-Entities können sich zwischen den Engines unterscheiden. Es wird keine nicht getestete Display-Entity-Parität versprochen.

## Technische Referenzen

- https://geysermc.org/wiki/geyser/custom-items/ – Mapping-v2-Vertrag, Legacy- und Modell-Definitionen
- https://geysermc.org/wiki/geyser/packs/ – Verteilung fertiger Bedrock-Packs
- https://github.com/GeyserMC/Rainbow – Vergleich der Geometrie-/Animationskonventionen; dessen bekannte Third-Person-X-Einschränkung wurde nicht übernommen
- https://github.com/AZPixel-Team/Java2Bedrock – Vergleich der getrennten Achsenhierarchie und Attachment-Rahmen

Der neue Python-Builder ist eine eigenständige Implementierung für dieses Pack. Ursprüngliche Modell-Credits bleiben in den Java-Quelldateien erhalten.

## Tatsächlicher Client-Test am 16.10.2026

Der genehmigte Proxy-Neustart installierte zunächst Pack-Version 1.21.12 (SHA256 f79c253dd28510de8ccdb377e2cf47d6edb9ab9eef38e1eb4a4e885f25ae28fe). Backup: `/home/cloudnet/enbackup/bedrock-pack-20261016/backup-20261016-164422`. Lobby, EnderGuns und Bauserver wurden dafür nicht neu gestartet. Das Java-Download-Pack und der ProxySystem-JAR blieben unverändert.

Im vorhandenen Windows-Bedrock-Client wurden echte Waffensymbole, texturierte 3D-NPC-Waffen, Munition und die M1014-Handansicht bestätigt. Der reale Test zeigte zugleich Fehler, die der native Ladetest nicht erkennen konnte: übergroße/verschobene Unicode-Bilder und eine unsichtbare M9-Handansicht. Diese Zwischenstände werden ausdrücklich nicht als fertige Modellparität gewertet.

Die Schriftkonvertierung verwendet nun Java-`height`/`ascent` und Bedrocks mittige Unicode-Zellenausrichtung. Version 1.21.14 zeigt in der Lobby RANK, PLAYER, COINS, PLAYTIME und das Community-Logo korrekt. Echter Screenshot: `evidence-bedrock-20261016/client-v14-lobby-fonts.png`. Die rote native Bedrock-Zeilennummerierung ist eine separate Protokoll-/Scoreboard-Eigenschaft und wurde nicht als Resourcepack-Fehler behandelt.

Das Content-Protokoll identifizierte zusätzlich ein übernommenes beschädigtes `textures/enderguns/bullet.png`: UTF-16-kodierte Binärdaten statt PNG. Die aktuelle Java-Sprite-Datei ersetzt diese Legacy-Referenz. Der Builder öffnet jetzt sämtliche PNGs zur Integritätsprüfung; ein Server-Regressionstest prüft zusätzlich Signatur und Chunk-CRCs.

M9-Kalibrierungen stehen getrennt in `bedrock-view-adjustments.json`, damit Java-Quellen nicht durch Kamerakorrekturen verändert werden. Die allgemeine Konvertierung bewahrt sämtliche drei Drehachsen. Die rechte M9-Handansicht in 1.21.15 verwendet ausdrücklich Pauls ältere vollständige 3D-Pose und deren Drehpunkt als manuelle Referenz; dies ist eine dokumentierte Ausnahme von der allgemeinen Umrechnung. Eine bloß mathematische Achsenprüfung gilt hierfür nicht als visuelle Abnahme.

20 Ressourcenprüfungen auf dem Server bestanden. Der Geyser-Reload wurde vorher mit der identischen Geyser-Version in einem isolierten Loopback-Prozess geprüft; anschließend wurden die produktiven Java-Prozess-IDs bei jeder reinen Pack-Korrektur unverändert nachgewiesen. Proxmox-SSH war vor dem letzten Lauf zeitweise nicht erreichbar, daher liefen die letzten reinen Dateiprüfungen isoliert unter `/home/cloudnet/enbackup/bedrock-asset-fixture-20261016` auf dem CloudNet-Host. Kein Minecraft-Testserver auf dem PC. Nachweise enthalten auch die anfänglich zu strengen Logger-/Ready-Muster und deren Korrektur; zusätzliche Proxy-Neustarts erfolgten deshalb nicht.

Noch offen: endgültige M9-Sichtabnahme und vollständiger Vergleich aller 21 Waffen in sämtlichen Haupt-/Nebenhand-, Kamera-, Schuss-/Nachlade- und Zoom-Kontexten. Das Pack ist installiert; eine vollständige 1:1-Parität aller Ansichten wird nicht behauptet.
