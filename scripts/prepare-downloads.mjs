import { copyFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

const root = resolve(import.meta.dirname, '..')
const output = resolve(root, 'public', 'downloads')
mkdirSync(output, { recursive: true })
for (const name of ['Invoke-SentinelAudit.ps1', 'Backup-Sentinel.ps1', 'Initialize-Sentinel.ps1']) {
  copyFileSync(resolve(root, 'scripts', name), resolve(output, name))
}
const packaged = spawnSync('python', [resolve(root, 'scripts', 'build-windows-setup.py')], { stdio: 'inherit' })
if (packaged.status !== 0) process.exit(packaged.status || 1)
