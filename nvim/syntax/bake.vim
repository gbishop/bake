" Keep the box borders grey
syn match Box /[│├─┼┤┬┴┘└┌┐]/
highlight Box guifg=#888888

highlight link PartText Type
" highlight link PartTotals Keyword
highlight PartHead guibg=#222244

" Grams column
syn match Grams /\v(^│[a-zA-Z ]+│\s+)@<=[-0-9.]+/
highlight link Grams Constant

" Error messages
syn match DiagnosticError /\v⚠.*$/

" Block and line comments
syntax region bComment start=/\v\/\*(\+)@!/ end=/\*\//
syntax match lComment /\v#.*$/
highlight bComment gui=italic
highlight lComment gui=italic
