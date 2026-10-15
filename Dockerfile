FROM python

LABEL version="2.0"
LABEL puplish="15.10.2026"

WORKDIR /Rep

COPY . .

RUN pip install -r requirement.txt

ENV PYTHONPATH=/Rep 
ENV DEBUG=1

EXPOSE 5000

CMD ["python", "app.py"]