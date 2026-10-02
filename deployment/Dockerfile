FROM python:3.12-slim
WORKDIR /app
COPY deployment/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY config ./config
COPY data/demo ./data/demo
COPY .streamlit ./.streamlit
COPY reports/exports/weekly_management_pack.xlsx ./reports/exports/weekly_management_pack.xlsx
COPY streamlit_app.py ./streamlit_app.py
COPY deployment/streamlit_app.py ./deployment/streamlit_app.py
ENV RESTOPS_MODE=public
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "deployment/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
