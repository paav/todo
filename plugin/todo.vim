" Vim global plugin for handling tasks
" Last Change:	2015 May 02
" Maintainer:	Alexey Panteleiev <paav at inbox dot ru>

if exists('g:loaded_todo')
    " finish
endif

let g:loaded_todo = 1

let s:old_cpo = &cpo
set cpo&vim

let s:BUFNAME_MAIN = 'TodoMain'
let s:MAINWIN_W = 65
let s:DIR_BASE = escape(expand('<sfile>:p:h:h'), '\')
let s:DIR_LIB = s:DIR_BASE . '/lib'

let s:FILE_DB = s:DIR_BASE . '/data/todo.db'

command! Todo call s:Open()
command! TodoToggle call s:Toggle()
command! TodoClose call s:Close()

let s:plugin_dir = escape(expand('<sfile>:p:h'), '\')
let s:base_dir = escape(expand('<sfile>:p:h:h'), '\')
let s:db = s:base_dir . '/data/todo.db'

augroup todo
    autocmd!
    exe 'autocmd BufNewFile ' . s:BUFNAME_MAIN . ' call s:ApplyMainBufSettings()'
    exe 'autocmd BufNewFile ' . s:BUFNAME_MAIN . ' call s:ApplyMainBufMaps()'
    autocmd BufEnter TodoAdd call s:TodoSettingsAdd()
    autocmd BufWinLeave TodoAdd call s:TodoSave()
    autocmd BufEnter TodoEdit call s:TodoSettingsAdd()
    autocmd BufWinLeave TodoEdit call s:TodoSave()
augroup END

function! s:WinIsVisible(bufname) abort
    if s:GetWinNum(a:bufname) != -1
        return 1
    endif
    return 0
endfunction


" Class HelpWidget
" ============================================================ 

let s:HelpWidget = {
    \'_TEXT_INFO': ['Press ? for help'],
    \'_TEXT_HELP': [
            \'"j": move cursor down',
            \'"k": move cursor up',
            \'"n": new task',
            \'"e": edit task'
        \]
\}

function! s:HelpWidget.create() abort
    let self._isvisible = 0
    let self._curtext = self._TEXT_INFO
    let self._prevtext = []
    return copy(self)
endfunction

function! s:HelpWidget.render() abort
    let l:save_opt = &l:modifiable
    let &l:modifiable = 1

    if !empty(self._prevtext) 
        let prev_text_len = len(self._prevtext)
        exe '1,' . prev_text_len . '$delete'
    endif

    call append(0, self._curtext)
    let self._isvisible = 1
    let &l:modifiable = l:save_opt
endfunction

function! s:HelpWidget.isVisible() abort
    return self._isvisible
endfunction

function! s:HelpWidget.toggle() abort
    if empty(self._prevtext)
        let self._prevtext = self._curtext
        let self._curtext = self._TEXT_HELP
    else
        let l:curtext_save = self._curtext
        let self._curtext = self._prevtext
        let self._prevtext = l:curtext_save
    endif
    
    call self.render()
endfunction


" Class TasksTableWidget
" ============================================================ 

let s:TasksTableWidget = {}

function! s:TasksTableWidget.create() abort
    let self._isvisible = 0
    let self._tasks = pyeval('tasklist.gettasks()')
    return copy(self)
endfunction

function! s:TasksTableWidget.render() abort
    let l:save_opt = &l:modifiable
    let &l:modifiable = 1
    " exe a:lnum . ',$delete'

    call self._renderHead()

    call self._renderBody()

    let self._isvisible = 1
    let &l:modifiable = l:save_opt
endfunction

function! s:TasksTableWidget._renderHead() abort
    let @o = printf('%-10s%-32s%-10s%-10s', 'Created', 'Title', 'Tag', 'Pri') 
    let @o .= "\n" . repeat('-', 60)
    put o
endfunction

function! s:TasksTableWidget._renderBody() abort
    let self._base_lnum = line('.') + 1
    for task in self._tasks
        call setline(line('.') + 1, self._tasktorow(task))
        call cursor(line('.') + 1, col('.'))
    endfor
endfunction

function! s:TasksTableWidget._tasktorow(task) abort
    " Pick only first tag
    let tag = get(a:task.tags, 0, {})
    let tagname = !empty(tag) ? tag.name : '' 

    return printf('%-13s%-32s%-10s%-5s',
        \self._tstotimeformat(a:task.create_date, '%-d %b'),
        \a:task.title, tagname, a:task.priority) 
endfunction

function! s:TasksTableWidget._tstotimeformat(ts, format)
    return pyeval(
        \'datetime.fromtimestamp(' . string(a:ts) . ').strftime("'
            \ . a:format . '")')
endfunction


function! s:Open() abort
        " python reload(todo)
    " if !exists('g:todo_py_loaded')
        python import sys
        exe 'python sys.path.append("' . s:DIR_LIB . '")'
        python import todo 
        python from todo import tasklist
        python from datetime import datetime
        exe 'python todo.setdb("' . s:FILE_DB . '")'
        let g:todo_py_loaded = 1
    " endif

    if s:WinIsVisible(s:BUFNAME_MAIN)
        return
    endif

    call s:OpenMainWin()
    setlocal modifiable
    1,$delete
    setlocal nomodifiable
    
    " if !exists('b:help_widget')
        let b:help_widget = s:HelpWidget.create()
    " endif

    " if !b:help_widget.isVisible()
        call b:help_widget.render()
    " endif

    let b:tasks_table = s:TasksTableWidget.create()
    call b:tasks_table.render()
endfunction

function! s:Close() abort
    call s:GotoWin(s:BUFNAME_MAIN)
    close
endfunction

function! s:GotoWin(bufname) abort
    exe s:GetWinNum(a:bufname) . 'wincmd w' 
endfunction

function! s:GetWinNum(bufname) abort
    return bufwinnr(bufnr(a:bufname))
endfunction

function! s:Toggle()
    if s:WinIsVisible(s:BUFNAME_MAIN)
        call s:Close()
    else
        call s:Open()
    endif
endfunction

function! s:OpenMainWin() abort
    exe 'topleft ' . s:MAINWIN_W . 'vnew ' . s:BUFNAME_MAIN
endfunction

function! s:TodoOpen()
    " TODO: replace with import
    exe 'pyfile ' . s:plugin_dir . '/todo.py'
    topleft 65vnew Todo 
    python render_tasks()
endfunction

function! s:TodoClose()
    exe bufwinnr(bufnr('Todo')) . "wincmd w"
    quit
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

function! s:ApplyMainBufMaps()
    nnoremap <script> <silent> <buffer> n :call <sid>TodoAdd()<cr>
    nnoremap <script> <silent> <buffer> d :call <sid>TodoDelete()<cr>
    nnoremap <script> <silent> <buffer> e :call <sid>TodoEdit()<cr>
    nnoremap <script> <silent> <buffer> = :call <sid>TodoIncPriority()<cr>
    nnoremap <script> <silent> <buffer> - :call <sid>TodoDecPriority()<cr>
    nnoremap <script> <silent> <buffer> d :call <sid>TodoFinish()<cr>
    nnoremap <script> <silent> <buffer> f :call <sid>TodoApplyTagFilter()<cr>
    nnoremap <silent> <buffer> ? :call b:help_widget.toggle()<CR>
endfunction

function! s:ApplyMainBufSettings()
    setlocal buftype=nofile
    setlocal noswapfile
    setlocal nobuflisted
    setlocal nomodifiable
    setlocal nonumber
    setlocal cursorline
    setlocal filetype=newtodo
    setlocal conceallevel=3
    setlocal concealcursor=nc
endfunction

function! s:TodoSettingsAdd()
    setlocal noswapfile
    setlocal nonumber
    setlocal nobuflisted
endfunction

let &cpo = s:old_cpo
unlet s:old_cpo
