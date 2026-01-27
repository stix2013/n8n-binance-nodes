ARG N8N_VERSION=2.6.0
FROM n8nio/runners:${N8N_VERSION}-amd64
USER root

RUN cd /opt/runners/task-runner-javascript && \
    pnpm add moment uuid @binance/spot @binance/common trading-signals
COPY n8n-task-runners.json /etc/n8n-task-runners.json

USER runner
