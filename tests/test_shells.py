"""Check shared startup under Bash and Zsh without loading this user's tools."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShellTests(unittest.TestCase):
    def startup(self, shell, platform):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            shutil.copytree(ROOT/'files/shared', home, dirs_exist_ok=True)
            bin_path = home/'bin'; bin_path.mkdir()
            uname = bin_path/'uname'
            uname.write_text('#!/bin/sh\nprintf "%s\\n" '+platform+'\n'); uname.chmod(0o755)
            sdk = home/('Library/Android/sdk' if platform=='Darwin' else 'Android/Sdk')
            (sdk/'emulator').mkdir(parents=True)
            (sdk/'platform-tools').mkdir()
            (home/'.local/bin').mkdir(parents=True)
            environment = {'HOME':str(home), 'PATH':str(bin_path)+':/usr/bin:/bin', 'TERM':'xterm', 'LANG':'C.UTF-8'}
            if shell=='bash':
                command=['bash','--noprofile','--norc','-ic', '. "$HOME/.bashrc"; alias dotfiles; printf "SDK=%s\\n" "$ANDROID_SDK_ROOT"; command -v avd; case ":$PATH:" in *":$HOME/.local/bin:"*) printf "PATH_OK\\n" ;; esac']
            else:
                executable = os.environ.get('DOTFILES_ZSH_TEST_COMMAND') or shutil.which('zsh')
                if not executable:
                    self.skipTest('Zsh is not installed; set DOTFILES_ZSH_TEST_COMMAND for the temporary runtime')
                environment['FPATH'] = os.environ.get('DOTFILES_ZSH_TEST_FPATH', '')
                modules = os.environ.get('DOTFILES_ZSH_TEST_MODULES', '')
                setup = 'module_path=("'+modules+'" $module_path); ' if modules else ''
                command=[executable,'-dfic', setup+'. "$HOME/.zshrc"; alias dotfiles; printf "SDK=%s\\n" "$ANDROID_SDK_ROOT"; command -v avd; case ":$PATH:" in *":$HOME/.local/bin:"*) printf "PATH_OK\\n" ;; esac']
            result=subprocess.run(command,env=environment,capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('dotfiles-sync',result.stdout)
            self.assertIn('SDK='+str(sdk),result.stdout)
            self.assertIn('avd',result.stdout)
            self.assertIn('PATH_OK',result.stdout)
            self.assertNotIn('not found',result.stderr)
            self.assertNotIn('no such file',result.stderr.lower())
            self.assertNotIn('Agent pid',result.stdout)

    def test_bash_linux_startup(self):
        self.startup('bash','Linux')

    def test_bash_macos_paths(self):
        self.startup('bash','Darwin')

    def test_zsh_linux_startup(self):
        self.startup('zsh','Linux')

    def test_zsh_macos_paths(self):
        self.startup('zsh','Darwin')


if __name__=='__main__':
    unittest.main()
