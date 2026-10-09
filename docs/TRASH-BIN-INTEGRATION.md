# Public trash bin

Item model: `endernation:trash_bin`. Original EnderNation cuboid model and 32x32 texture.

Corrected Java UVs are in 0..16, quarter-turn elements are baked into geometry, outside wall and pictogram are present. Open top is intentional. `fixed` display has translation [0,8,0] and scale [1,1,1]; with FIXED and identity entity transform its bottom is at the display origin, height 0.8990353 blocks. Orient front towards -Z.

Use FIXED at block top. Current first plugin trial still uses a 0.75 scale at +0.34 and a raised Interaction; alignment follow-up is pending separately. No Minecraft live rendering acceptance yet.

This patch preserves every preexisting asset, including the normal Minecraft font and all guns.
