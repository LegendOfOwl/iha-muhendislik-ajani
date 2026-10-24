const path = require('path');
const fs = require('fs');
const root = path.resolve(__dirname, '../..');
process.env.XDG_CACHE_HOME = path.join(root, 'work/cache');
const fontCache = path.join(root, 'work/cache/fontconfig');
fs.mkdirSync(fontCache, {recursive: true});
const fontConfig = path.join(root, 'work/cache/fonts.conf');
fs.writeFileSync(fontConfig, `<?xml version="1.0"?><fontconfig><dir>C:/Windows/Fonts</dir><cachedir>${fontCache.replaceAll('\\', '/')}</cachedir></fontconfig>`);
process.env.FONTCONFIG_FILE = fontConfig;
const sharp = require('C:/Users/Urungu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async () => {
  await sharp(path.join(root, 'outputs/cad/aircraft_three_view.svg'), {density: 120})
    .resize({width: 1680}).png().toFile(path.join(root, 'outputs/plots/aircraft_three_view.png'));
  console.log('Three-view drawing preview rendered.');
})().catch(error => { console.error(error); process.exitCode = 1; });
