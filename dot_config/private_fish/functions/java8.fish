function java8 --description 'java with JDK 8'
    set -l jh (/usr/libexec/java_home -v 1.8)
    "$jh/bin/java" $argv
end
