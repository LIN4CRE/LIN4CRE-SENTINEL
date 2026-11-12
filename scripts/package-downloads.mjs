import { copyFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

const root = resolve(import.meta.dirname, '..')
const packaged = spawnSync('python', [resolve(root, 'scripts', 'build-windows-setup.py')], {
  cwd: root,
  stdio: 'inherit',
})

if (packaged.error) throw packaged.error
if (packaged.status !== 0) process.exit(packaged.status ?? 1)

const archive = resolve(root, 'public', 'downloads', 'LIN4CRE-SENTINEL-Windows-Setup.zip')
const distDownloads = resolve(root, 'dist', 'downloads')
mkdirSync(distDownloads, { recursive: true })
copyFileSync(archive, resolve(distDownloads, 'LIN4CRE-SENTINEL-Windows-Setup.zip'))
