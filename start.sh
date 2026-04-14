#!/bin/bash

#Start backend
#uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

#Start streamlit
#streamlit run frontend_streamlit.py --server.port $PORT --server.address 0.0.0.0

#!/bin/bash
streamlit run streamlit_app.py --server.port 8000 --server.address 0.0.0.0