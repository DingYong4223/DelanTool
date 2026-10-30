function mvn8 --description 'mvn with JDK 8'
    env JAVA_HOME=(/usr/libexec/java_home -v 1.8) mvn $argv
end
