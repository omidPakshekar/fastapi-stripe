FROM python:3.10.5-slim
WORKDIR /stripe
COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r /stripe/requirements.txt

COPY . /stripe

## program run methods
CMD ["uvicorn", "Stripe:app", "--host" , "0.0.0.0" , "--port" , "5022"]
