" Vim syntax file for vim-todo plugin
" Last Change:	2015 May 10
" Maintainer:	Alexey Panteleiev <paav at inbox dot ru>

if exists('b:current_syntax')
  finish
endif

syntax clear

syntax match ntodoTableHead /^\~.*/ contains=ntodoIgnore
syntax match ntodoComment /".*/
syntax match ntodoTableDelim /─\+/
syntax match ntodoTableRow /^`.*/ contains=ntodoIgnore,ntodoTableMarkedCell,
                                          \ntodoErrPri,ntodoWarnPri
syntax match ntodoTableMarkedCell /\v(\zs.{-1,}\s{2,}){2}/ contained
syntax match ntodoHelp /^".*/ contains=ntodoIgnore
syntax match ntodoIgnore /\v([`~"]|!\d)/ contained conceal 
syntax match ntodoErrPri /!1.*/ contains=ntodoIgnore
syntax match ntodoWarnPri /!2.*/ contains=ntodoIgnore

highlight link ntodoTableHead Normal
highlight link ntodoComment Comment
highlight link ntodoTableDelim Normal
highlight link ntodoTableMarkedCell Normal
highlight link ntodoHelp Comment
highlight link ntodoErrPri Special
highlight link ntodoWarnPri Type

let b:current_syntax = 'todo'
