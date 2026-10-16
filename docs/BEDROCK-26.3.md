# Bedrock-Kompatibilität: Entwicklungskandidat 16.10.2026

**Gebaut und auf dem Server geprüft, noch nicht installiert.** Die exakte Darstellung mit Java- und Bedrock-Clients steht zur Abnahme aus. Das native Geyser-Prüfprogramm bestätigt keine identische Kamera-/Handdarstellung.

## Grundlage

Das aktuell ausgelieferte Java-Pack verweist auf dieses Repository und den Release-Tag `update-26.3`. Grundlage der neuen `ai-dev`-Arbeiten ist `76585cb` (inklusive halbierter Sounds und bestehender Mülltonne). Das ältere Repository `EnderNationTeam/minecraft-resource-pack`, Stand `e1b0ab9`, diente als 3D-/Animationsreferenz; es wurde nicht mit alten Java-Dateien über den aktuellen Stand kopiert.

Die vorherige aktive Bedrock-Fassung verwendete für die Waffen eine gemeinsame flache Ersatzgeometrie. Die ältere 3D-Fassung enthielt veraltete Haltewerte. Jetzt werden Geometrien, Drehpunkte, Texturen, UVs und vollständige XYZ-Ansichten aus den aktuellen Java-Modellen erzeugt. Für jeden Kontext gibt es eigene Haupt-/Nebenhand-Ansichten sowie Kopfansicht und Ausblenden am eigenen Kopf. Insbesondere wird die X-Drehung der Third-Person-Ansicht nicht mehr verworfen.

## Inhalt

- 32 Modelle: 21 Waffen sowie Munition, Projektil, Hilfsitems und Mülltonne. Jede echte Java-Kuboid-Geometrie bleibt als echte Bedrock-Kuboid-Geometrie erhalten. Flache Vanilla-Hilfsitems werden anhand ihrer tatsächlichen transparenten Texturen extrudiert.
- 62 eindeutige Geyser-v2-Definitionen für vorhandene Custom-Model-Data- und `item_model`-Varianten. Die 31 bisherigen `geyser_custom:eg_*`-IDs bleiben kompatibel; zusätzliche Modellvarianten erhalten eigene IDs. Das Projektil besitzt ausschließlich die tatsächlich vorhandene CMD-Variante.
- Eigene Inventarsymbole aus den Java-GUI-Ansichten, anstatt den Textur-Atlas als Inventarsymbol zu zeigen.
- Alle 32 enthaltenen Sounddateien einschließlich Lautstärke 0,5 sowie 73 private Unicode-Glyphen aus dem aktuellen Java-Pack.
- Bestehende Pack-UUIDs bleiben erhalten; die Pack-Version steigt von `[1,21,11]` auf `[1,21,12]`, damit Clients den neuen Stand laden.
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

Öffentlicher Bedrock-Zugang benötigt UDP 19132 zur Proxy-Adresse 10.0.1.205:19132; diese Weiterleitung war in der bisherigen Prüfung nicht nachgewiesen. Die Firewall-Verwaltung bleibt beim Nutzer/Developer. Über bereits vorhandenen internen Netzwerkzugang lässt sich die Proxy-Adresse direkt testen.

## Verbindliche Client-Abnahme

Mit Java und Bedrock alle Waffen vergleichen: First-/Third-Person, Haupt-/Nebenhand und linke dominante Hand, Schießen, Nachladen, Zoom, Verzauberungsglanz und Projektiltextur. Die genaue Kamera-/Handbasis und enginebedingte Unterschiede sind erst damit bestätigt. Die Datenkonvertierung beweist keine Pixelgleichheit.

Bedrocks private Font-Zellen können die sehr breiten Java-Schilder/Logos nicht zwangsläufig in identischer Breite und Höhe darstellen. Die Glyphen sind enthalten; die Lesbarkeit muss im Client geprüft werden. Inventar-/Boden-Itemdarstellung und Display-Entities können sich zwischen den Engines unterscheiden. Es wird keine nicht getestete Display-Entity-Parität versprochen.

## Technische Referenzen

- https://geysermc.org/wiki/geyser/custom-items/ – Mapping-v2-Vertrag, Legacy- und Modell-Definitionen
- https://geysermc.org/wiki/geyser/packs/ – Verteilung fertiger Bedrock-Packs
- https://github.com/GeyserMC/Rainbow – Vergleich der Geometrie-/Animationskonventionen; dessen bekannte Third-Person-X-Einschränkung wurde nicht übernommen
- https://github.com/AZPixel-Team/Java2Bedrock – Vergleich der getrennten Achsenhierarchie und Attachment-Rahmen

Der neue Python-Builder ist eine eigenständige Implementierung für dieses Pack. Ursprüngliche Modell-Credits bleiben in den Java-Quelldateien erhalten.
