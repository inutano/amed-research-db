#!/bin/bash
# Start the AMED Research Database API

cd "$(dirname "$0")"
echo "Starting AMED Research Database API..."
echo "API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
python api/main.py
