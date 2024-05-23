cd ../BackEnd
start python3 app.py
%SendKeys% {Enter}
cd ../scheduler
timeout /t 10 /nobreak
start python3 main.py