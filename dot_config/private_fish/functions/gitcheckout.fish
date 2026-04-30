function gitcheckout
    git checkout $(git branch | fzf | xargs)
end
