# nginx-analyzer
Analyses logs of nginx

# Before running the container build the image 
docker build -t nginx-analyzer .

# How to run it on Linux
docker run -v $(pwd):/app nginx-analyzer --input access.log --output result.csv

# On Windows in cmd.exe
docker run -v "%cd%:/app" nginx-analyzer --input access.log --output report.csv --chart analytics.png