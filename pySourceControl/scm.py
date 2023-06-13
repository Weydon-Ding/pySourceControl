# -*- coding: utf-8 -*-
from os import listdir, remove
from os.path import abspath, isdir, isfile, join
from platform import system
from re import compile, findall
from subprocess import PIPE, STDOUT, run


class SCM(object):
    __shell = system() != 'Windows'

    def __init__(self, local:str=None, remote:str=None):
        self.local = local
        self.remote = remote
        if self.remote is None:
            self.remote = self.__get_remote_from_local()

    @property
    def type(self)->str:
        local_type = self.__get_type_from_local()
        remote_type = self.__get_type_from_remote()
        if local_type and remote_type:
            if local_type != remote_type:
                raise Exception(f'local_type {local_type} != remote_type {remote_type}')
        return local_type or remote_type

    def __get_remote_from_local(self)->str:
        if self.local:
            if self.type == 'svn':
                p = run(f'svn info "{self.local}"', stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
                if p.returncode == 0:
                    return findall(compile('URL: (.+)\s'), str(p.stdout.decode('gbk')))[0].strip()
            elif self.type == 'git':
                p = run(f'git remote -v', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
                if p.returncode == 0:
                    return findall(compile(f'origin\s(.+)\s\(fetch\)'), str(p.stdout.decode()))[0]
        return None

    def __get_type_from_local(self)->str:
        if self.local and isdir(self.local):
            p = run(f'svn info "{self.local}"', stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            if p.returncode == 0:
                return 'svn'
            p = run('git rev-parse --short HEAD', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            if p.returncode == 0:
                return 'git'
        return None

    def __get_type_from_remote(self)->str:
        if self.remote:
            if '/svn/' in self.remote:
                return 'svn'
            elif self.remote.endswith('.git'):
                return 'git'
        return None

    def checkout(self)->bool:
        if self.type == 'svn':
            p = run(f'svn checkout "{self.remote}" "{self.local}"', shell=SCM.__shell)
        elif self.type == 'git':
            p = run(f'git clone "{self.remote}" "{self.local}"', shell=SCM.__shell)
        return p.returncode == 0

    def switch(self, branch:str)->bool:
        if branch is None:
            return False
        if self.type == 'svn':
            p = run(f'svn switch {branch}', cwd=self.local, shell=SCM.__shell)
        elif self.type == 'git':
            p = run('git fetch --progress -v "origin"', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            if p.returncode == 0:
                p = run(f'git switch {branch}', cwd=self.local, shell=SCM.__shell)
        return p.returncode == 0

    def revert(self, path:str=''):
        if self.type == 'svn':
            run(f'svn cleanup "{self.local}"', stdout=PIPE, stderr=STDOUT, shell=SCM.__shell) # use cleanup to release lock
            run(f'svn revert -R "{abspath(join(self.local, path))}"', shell=SCM.__shell)
        elif self.type == 'git':
            work_dir = join(self.local, path)
            run('git merge --abort', cwd=work_dir, stderr=PIPE, shell=SCM.__shell)  # revert conflict
            run('git restore .', cwd=work_dir, shell=SCM.__shell)                   # revert modified
            run('git restore --staged .', cwd=work_dir, shell=SCM.__shell)          # revert added

    def cleanup(self):
        if self.type == 'svn':
            run(f'svn cleanup --remove-unversioned "{self.local}"', shell=SCM.__shell)
        elif self.type == 'git':
            run('git clean -d -fx', cwd=self.local, shell=SCM.__shell)

    def update(self, revision:str=''):
        revision = revision or '' # 防止None值
        revision = revision.strip()
        if self.type == 'svn':
            if revision:
                run(f'svn update "{self.local}" -r {revision}', shell=SCM.__shell)
            else:
                run(f'svn update "{self.local}"', shell=SCM.__shell)
        elif self.type == 'git':
            run('git pull --progress -v --no-rebase "origin"', cwd=self.local, shell=SCM.__shell)
            run(f'git reset --hard {revision}', cwd=self.local, shell=SCM.__shell)

    def add(self, file:str):
        if self.type == 'svn':
            p = run(f'svn add {file} --force', cwd=self.local, shell=SCM.__shell)
            p = run('cmd.exe /c svn status | find "!"', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            missing_files = p.stdout.decode().strip().replace('!       ', '').splitlines()
            for missing_file in missing_files:
                p = run(f'svn delete {missing_file}', cwd=self.local, shell=SCM.__shell)
        elif self.type == 'git':
            pass
        else:
            pass

    def commit(self, msg:str):
        if self.type == 'svn':
            run(f'svn commit -m "{msg}"', cwd=self.local, shell=SCM.__shell)
            run('svn status | find "!"', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
        elif self.type == 'git':
            pass
        else:
            pass

    @property
    def revision(self)->str:
        if self.type == 'svn':
            p = run(f'svn info "{self.local}"', stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            return findall(compile('Last Changed Rev: ([0-9]+)'), str(p.stdout))[0]
        elif self.type == 'git':
            p = run('git rev-parse --short HEAD', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            return p.stdout.decode().strip()
        else:
            return '    '

    def get_latest_revision(self, branch:str)->str:
        if self.type == 'svn':
            p = run(f'svn info "{branch}"', stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            return findall(compile('Last Changed Rev: ([0-9]+)'), str(p.stdout))[0]
        elif self.type == 'git':
            p = run(f'git ls-remote "{self.remote}" refs/heads/{branch}', cwd=self.local, stdout=PIPE, stderr=STDOUT, shell=SCM.__shell)
            return findall(compile(f'([A-Za-z0-9]+)\s+refs/heads/{branch}'), str(p.stdout.decode()))[0][0:9]
        else:
            return '    '

    def unlock(self):
        if self.type == 'svn':
            pass
        elif self.type == 'git':
            lock = join(self.local, '.git', 'index.lock')
            if isfile(lock):
                remove(lock)


def init_repo(scm:SCM, branch:str, revision:str=''):
    if not isdir(scm.local) or len(listdir(scm.local)) == 0:
        scm.checkout()
    else:
        scm.unlock()
        scm.revert()
        scm.cleanup()
    scm.switch(branch)
    scm.update(revision)


__all__ = ['SCM', 'init_repo']
