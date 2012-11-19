# MOM: My own manual (aka My options memorizer aka My optional memory)

Create your own help files with colors.

## Tips

1. Create symbolic link, alias, or simply rename to `mom`.
2. Add `complete -c mom` to your `.bashrc` to have an autocompletion of commands (see also tip 4)
3. Put the folder with your help files to Dropbox by setting `InfoDir = ~/Dropbox/mom` in your `~/.momrc`.
4. To have a more advance autocompletion add the following code to your `.bashrc`

Here is the code:

    #  Completion for mom:
    #
    #  mom [command] [option]
    #
    _mom() 
    {
      local dirmom=${HOME}/Dropbox/mom
      local ext=.m0m
      local cur prev opts progname
      COMPREPLY=()
      cur="${COMP_WORDS[COMP_CWORD]}"
      prev="${COMP_WORDS[COMP_CWORD-1]}"
      opts="add edit ls rm"
      progname="${COMP_WORDS[0]}"

      case "${prev}" in
        ${progname})
          # already known commands
          local coms=$(for x in `ls -1 ${dirmom}/*${ext}`; do y=${x#*${dirmom}\/}; echo ${y%${ext}*}; done )
          COMPREPLY=( $(compgen -W "${coms}" -- ${cur}) )     
          return 0
            ;;
        -)
          opts="ls";;
        *);;
      esac 
      # options
      COMPREPLY=( $(compgen -W "${opts}" -- ${cur} ) )
    }
    complete -F _mom mom

