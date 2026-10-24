import { mkdir, copyFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
const output = new URL('../public/data/', import.meta.url)
await mkdir(output, { recursive: true })
for (const name of ['meta', 'forecast', 'backtest', 'history', 'rewards', 'live_record']) {
  await copyFile(fileURLToPath(new URL(`../../data/site/${name}.json`, import.meta.url)), fileURLToPath(new URL(`${name}.json`, output)))
}

const figuresOutput = new URL('../public/figures/', import.meta.url)
await mkdir(figuresOutput, { recursive: true })
for (const name of ['q1_category_share_by_year.png', 'q2_cycle_hist.png', 'q3_discontinued_by_category.png', 'q8_rewards_per_session.png']) {
  await copyFile(fileURLToPath(new URL(`../../outputs/figures/${name}`, import.meta.url)), fileURLToPath(new URL(name, figuresOutput)))
}
