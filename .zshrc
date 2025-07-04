eval PATH="$(bash --norc -ec 'IFS=:; paths=($PATH); 
for i in ${!paths[@]}; do 
if [[ ${paths[i]} == "''/Users/lawrence/.pyenv/shims''" ]]; then unset '\''paths[i]'\''; 
fi; done; 
echo "${paths[*]}"')"
export PATH="/Users/lawrence/.pyenv/shims:${PATH}"
command pyenv rehash 2>/dev/null
