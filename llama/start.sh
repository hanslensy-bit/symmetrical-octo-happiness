#!/bin/bash
./llama-server -hf mradermacher/Llama-3.2-1B-Instruct-Abliterated-GGUF:Llama-3.2-1B-Instruct-Abliterated.Q4_K_M.gguf --port 8080 -c 2048 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3
python3 router.py "$@"
kill $SERVER_PID
