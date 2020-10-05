FROM python
RUN mkdir /app
COPY server.py /app/
WORKDIR /app
RUN pip install flask
#EXPOSE 8080
#ENV FLASK_APP=server.py
#CMD flask run --host=0.0.0.0
CMD [ "python", "./server.py" ]