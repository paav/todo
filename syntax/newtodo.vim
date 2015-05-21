" Vim syntax file for vim-todo plugin
" Last Change:	2015 May 10
" Maintainer:	Alexey Panteleiev <paav at inbox dot ru>

if exists('b:current_syntax')
  finish
endif

syntax clear

syntax match ntodoHelp /^".*/ contains=ntodoIgnore
syntax match ntodoIgnore /\v^["?!]/ contained conceal 
syntax match ntodoErrPri /^!.*/ contains=ntodoIgnore
syntax match ntodoWarnPri /^?.*/ contains=ntodoIgnore

highlight link ntodoHelp Comment
highlight link ntodoErrPri Special
highlight link ntodoWarnPri Type

let b:current_syntax = 'newtodo'
