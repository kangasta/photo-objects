FROM python:3.10-slim

WORKDIR /work/
RUN pip install yaml-requests
COPY photos/* ./photos/
COPY data.yml cleanup-demo.yml initialize-demo.yml wait-until-api-ready.yml entrypoint.sh ./

ENTRYPOINT [ "./entrypoint.sh" ]
