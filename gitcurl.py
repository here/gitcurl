#!/home/known/a/code/py/pyreqgit/env3.3/bin/python

## config
# todo: config in config file
# todo: support *arg sys.argv[] overrides
# todo: make a class object
# pypath = path/to/modules
# repopath = path/to/gitdir to git repo, 
# repofile = file to save request/curl output
pypath = '/home/known/a/code/py/pyreqgit/env3.3/lib/python3.3/site-packages'
repopath = '/home/known/a/code/py/pyreqgit/weburbanist.com'
repopath = repopath.rstrip('/') # strip trailing slashes
repofile = 'index.html'
siteuri = 'http://weburbanist.com'
useragent = 'pyreqgit'

# hard path to venv modules fixes imports from cron and scripts
import sys
sys.path.insert(0, pypath)

# wrapper for subprocesses including arbitrary shell commands
# http://amoffat.github.io/sh/
from sh import git, curl

# regular expressions
# https://docs.python.org/3.5/library/re.html
import re

# socket libraries
# http://docs.python-requests.org/en/latest/user/quickstart/#make-a-request
import requests

import string
import pprint as pp # prettyprint

def get_response(url=siteuri, timeout=45):

    headers = {'User-Agent': useragent}

    # response from siteuri using requests
    # on timeout raises requests.exceptions.Timeout
    response = requests.get(url, headers=headers, timeout=timeout)

    # raise exception on http status 4xx or 5xx
    # todo: try catch for error variants based on status code
    response.raise_for_status()

    return response


## write to file
def write(path, filename, text):
    outfile = path+'/'+filename
    out = open(outfile, 'w', encoding='utf-8')
    w = out.write(text)
    # out.flush()
    out.close()
    return w


# reset git to prepare for writing
def git_repo(repopath=repopath):
    return git.bake(_cwd=repopath)


# checkout branch
def git_checkout(repo, branch='master'):
    changes = repo_dirty(repo)
    if bool(changes):
        raise Exception('git_checkout(): repo is dirty')
    else:
        repo.checkout(branch)
        # todo: check for other errors here

    return repo


def repo_path(repo):
    return repr(repo('rev-parse','--show-toplevel')).strip()


# returns a regex search result object with .string attribute
def repo_dirty(repo):
    changes = []
    # repostatus = repo.status('--porcelain')
    repostatus = repo.status('-z')
    for line in repostatus.split('\0'):
        if (not line): continue
        change = line.split()
        # put filename first to use as dictionary
        change.reverse()
        changes.append(change)

    pp.pprint(changes)
    return dict(changes)

    # modified = re.search('[ M][ M]', repr(repostatus))
    # untracked = re.search('[ ?][ ?]', repr(repostatus))

    # return modified or untracked


## check git for changes 
## checkout appropriate branch
## commit
## merge branch into master
def commit(repo, branch='static', message='default message'):

    changes = repo_dirty(repo)

    # look for changed files other than headers
    content_changes = [index for index, filename in enumerate(changes) if filename != 'headers']

    # if changes
    if changes:
        if len(content_changes): branch = 'changes'
        else: branch = 'headers'

        print("changes on branch "+branch)
        pp.pprint(changes)

        # stash -u includes untracked
        repo.stash('-u')

        # todo: fix checkout for new branches '-B' or similar
        repo.checkout(branch)
        repo.merge('master')
        repo.stash('pop')
        repo.add('-A')
        message = "branch: "+branch+"\n\n"+pp.pformat(changes,width=1)
    else:
        print("no changes")
        repo.checkout(branch) # previously as suspected
        repo.merge('master')
        message = "branch: "+branch+"\n\n"+"auto-static"

    diff = repo('--no-pager', 'diff', '--cached')
    repo.commit('-a', '--allow-empty', '-m', message)

    repo.checkout('master')
    repo.merge(branch)

    return diff



def main():

    if len(sys.argv) > 0:
        for arg in sys.argv:
            assert isinstance(arg, str)
            print(arg)

    # init response
    response = get_response(siteuri)

    # init repo
    repo = git_repo(repopath)

    # todo: assert repopath = git _cwd or fail to avoid overwriting app.py git repo
    if repo_path(repo) != repopath:
        raise Exception('main():' + repo_path(repo) + '!= repopath')

    # checkout master
    repo = git_checkout(repo)

    # write the new http requests to the git working directory
    write(repopath, repofile, response.text)
    write(repopath,'headers',pp.pformat(response.raw.headers))
    # todo: check response.history follow and test 301 redirects

    # todo: return value should be a full git object similar to response from requests module above
    diff = commit(repo)

    print('exit:'+repr(not bool(repr(diff))))
    print('diff:'+repr(diff))
    sys.exit(not bool(repr(diff)))

if __name__ == '__main__':
    # print('main')
    main()

