FROM mcr.microsoft.com/playwright:v1.51.1-noble

ENV CI=true

WORKDIR /tests
COPY entrypoint.sh *.json *.ts ./
RUN npm ci
COPY e2e/* ./e2e/
COPY photos/* ./photos/

ENTRYPOINT [ "./entrypoint.sh" ]
