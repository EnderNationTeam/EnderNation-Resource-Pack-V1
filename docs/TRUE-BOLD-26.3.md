# EnderNation true bold font contract (Minecraft Java 26.3)

Resource-pack font IDs:
- `endernation:regular` = Lato Regular 400
- `endernation:bold` = Lato Bold 700

Both fonts fall back to `minecraft:default` only for glyphs not present in Lato, which preserves the existing EnderNation private-use/UI bitmap glyphs.

## MiniMessage usage

Normal:
`<font:endernation:regular>Hier findest du Shop & Kits.</font>`

True bold:
`<font:endernation:bold>Menü</font>`

Mixed:
`<font:endernation:regular>Normal <font:endernation:bold>Fett</font> normal</font>`

Do not add `<bold>` inside `endernation:bold`: the font file itself is already Bold 700. Leaving Minecraft synthetic bold enabled would reintroduce the double-stroke effect.

## Plugin output transformer contract

Existing authoring syntax such as MiniMessage `<bold>` or legacy `&l` may remain as input, but before a component is sent/rendered the plugin must transform ordinary text styles:

1. Traverse the Adventure component tree recursively while preserving the component type.
2. Track inherited/effective `TextDecoration.BOLD` state (TRUE/FALSE/NOT_SET) and inherited font.
3. For ordinary text using no explicit special font, `minecraft:default`, `endernation:regular`, or `endernation:bold`:
   - effective bold TRUE -> set font `endernation:bold`, set BOLD explicitly FALSE.
   - effective bold FALSE -> set font `endernation:regular`, keep/set BOLD FALSE.
4. A child that explicitly resets bold must restore `endernation:regular`.
5. Explicit non-text/special glyph fonts must not be replaced.
6. Preserve colors, italic/underline/strikethrough/obfuscated states, insertion, click events, hover events, translatable keys and translatable arguments. Do not serialize to plain/legacy text and rebuild.
7. Recurse into ordinary children and type-specific embedded components/arguments rather than flattening the component.

The transformed render-ready component therefore uses a real Bold TTF with synthetic BOLD=false. This is an output adaptation layer, not a change to authoring syntax.

## Citizens boundary

A Citizens name path that is stored/handled only as a legacy/String NPC name must not be assumed to preserve an Adventure font key. For those NPCs, use a component-capable hologram/display path or an integration that passes the Adventure Component to the final entity/name renderer. Verify the installed Citizens build/path before relying on MiniMessage font tags in an NPC name.

## Vanilla UI boundary

Vanilla-owned bold UI strings still use Minecraft's synthetic bold on `minecraft:default`. A server resource pack cannot globally make vanilla `bold:true` automatically choose `endernation:bold`.
