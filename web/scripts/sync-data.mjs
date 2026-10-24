import { mkdir, copyFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
const output = new URL('../public/data/', import.meta.url)
await mkdir(output, { recursive: true })
for (const name of ['meta', 'forecast', 'backtest', 'history', 'rewards']) {
  await copyFile(fileURLToPath(new URL(`../../data/site/${name}.json`, import.meta.url)), fileURLToPath(new URL(`${name}.json`, output)))
}
