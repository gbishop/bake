" Keep the box borders grey
syn match Box /[│├─┼┤┬┴┘└┌┐]/
highlight Box guifg=#888888

syn match Headings /\v^│(\s+[a-z%]+\s+│){6,}/ contains=Box

" Parts: text in cells on rows that do not begin with an empty cell.
syn match PartText /\v(^│.*)@<=&(^│\s+│.*)@<![-a-z0-9.]+/ contains=Box
" highlight PartText guifg=#ffffcc
highlight link PartText Type

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

" part name
syntax match PartName /\v^[a-z_A-Z0-9]+(\s*\^\s*\d+[%g])?:/
highlight link PartName Type
