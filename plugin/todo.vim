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
    autocmd BufEnter Todo call s:TodoSettings()
    autocmd BufEnter Todo call s:TodoRefresh()
    autocmd BufEnter TodoAdd call s:TodoSettingsAdd()
    autocmd BufWinLeave TodoAdd call s:TodoSave()
    autocmd BufEnter TodoEdit call s:TodoSettingsAdd()
    autocmd BufWinLeave TodoEdit call s:TodoSave()
augroup END

function! s:TodoOpen()
    " TODO: replace with import
    exe 'pyfile ' . s:plugin_dir . '/todo.py'
    topleft 65vnew Todo 
    python render_tasks()
endfunction

function! s:TodoAdd()
    python add()
endfunction

function! s:TodoSave()
    python save()
endfunction

function! s:TodoDelete()
    python delete()
endfunction

function! s:TodoEdit()
    python edit()
endfunction

function! s:TodoIncPriority()
    python priority_add(1)
endfunction

function! s:TodoDecPriority()
    python priority_add(-1)
endfunction

function! s:TodoRefresh()
    python refresh()
endfunction

function! s:TodoFinish()
    python finish()
endfunction

function! s:TodoApplyTagFilter()
    python apply_tag_filter()
endfunction

function! s:TodoMappings()
    nnoremap <script> <silent> <buffer> n :call <sid>TodoAdd()<cr>
    nnoremap <script> <silent> <buffer> d :call <sid>TodoDelete()<cr>
    nnoremap <script> <silent> <buffer> e :call <sid>TodoEdit()<cr>
    nnoremap <script> <silent> <buffer> = :call <sid>TodoIncPriority()<cr>
    nnoremap <script> <silent> <buffer> - :call <sid>TodoDecPriority()<cr>
    nnoremap <script> <silent> <buffer> d :call <sid>TodoFinish()<cr>
    nnoremap <script> <silent> <buffer> f :call <sid>TodoApplyTagFilter()<cr>
endfunction

function! s:TodoSettings()
    setlocal buftype=nofile
    setlocal bufhidden=wipe
    setlocal noswapfile
    setlocal nobuflisted
    setlocal nomodifiable
    setlocal filetype=newtodo
    setlocal nonumber
    setlocal cursorline
    call s:TodoMappings()
endfunction

function! s:TodoSettingsAdd()
    setlocal noswapfile
    setlocal nonumber
    setlocal nobuflisted
endfunction

let &cpo = s:old_cpo
unlet s:old_cpo
