" Vim global plugin for handling tasks
" Last Change:	2015 May 02
" Maintainer:	Alexey Panteleiev <paav at inbox dot ru>

if exists('g:loaded_todo')
    " finish
endif

let g:loaded_todo = 1

let s:old_cpo = &cpo
set cpo&vim

if !exists(":Todo")
  command Todo call s:TodoOpen()
endif

let s:plugin_dir = escape(expand('<sfile>:p:h'), '\')
let s:base_dir = escape(expand('<sfile>:p:h:h'), '\')
let s:db = s:base_dir . '/data/todo.db'

augroup Todo
    autocmd!
    autocmd BufNewFile Todo call s:TodoSettings()
augroup END

function! s:TodoOpen()
    exe 'pyfile ' . s:plugin_dir . '/todo.py'
    topleft vnew Todo 
    python renderTasks()
endfunction

function! s:TodoSettings()"{{{
    setlocal buftype=nofile
    setlocal bufhidden=wipe
    setlocal noswapfile
    setlocal nobuflisted
    setlocal nomodifiable
    setlocal filetype=newtodo
    setlocal nonumber
endfunction"}}}

let &cpo = s:old_cpo
unlet s:old_cpo
