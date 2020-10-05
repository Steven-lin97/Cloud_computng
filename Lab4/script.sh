#!/bin/zsh
docker build -t lab4-img:latest .
docker run -d --name=lab4-app -p 0:8080 lab4-img:latest
docker port lab4-app | while IFS=: read  a b; do echo "localhost:$b"; done